import asyncio
import secrets

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnected
from fastapi.encoders import jsonable_encoder

from app.database import DatabaseError
from app.exceptions import RecursoNoEncontrado
from app.services.estado_service import EstadoService
from app.websocket.eventos import crear_evento
from app.websocket.manager import manager
from app.config import settings
from app.services.ws_ticket_service import WsTicketService

router = APIRouter()
estados = EstadoService()


@router.websocket("/ws/vehiculos/{id_vehiculo}")
async def monitorear_vehiculo(websocket: WebSocket, id_vehiculo: int):
    """Monitoreo en tiempo real de un vehículo. """

    # Autenticacion original mediante API Key.
    clave = websocket.headers.get("x-api-key")

    api_key_valida = bool(
        clave
        and secrets.compare_digest(
            clave.encode(), settings.api_key.encode()
        )
    )

    autorizado = api_key_valida

    # Autenticacion mediante ticket temporal de SCARLETTE.
    if not autorizado:
        origen = websocket.headers.get("origin")

        # Los tickets solo se aceptan desde GitHub Pages.
        if origen != "https://mf-estefania.github.io":
            await websocket.close(code=1008)
            return

        ticket = websocket.query_params.get("ticket")

        if ticket:
            servicio_tickets = WsTicketService()
            autorizado = await asyncio.to_thread(
                servicio_tickets.consumir_ticket,
                ticket,
                id_vehiculo,
            )

    if not autorizado:
        await websocket.close(code=1008)
        return

    await manager.conectar(id_vehiculo, websocket)
    try:
        try:
            estado = await asyncio.to_thread(estados.obtener, id_vehiculo)
        except RecursoNoEncontrado:
            await manager.enviar(
                websocket, crear_evento("error", id_vehiculo, mensaje="El vehículo no existe")
            )
            await websocket.close(code=4404)
            return
        except DatabaseError:
            await manager.enviar(
                websocket,
                crear_evento("error", id_vehiculo, mensaje="Servicio de datos no disponible"),
            )
            await websocket.close(code=1011)
            return

        await manager.enviar(
            websocket,
            crear_evento(
                "estado_inicial",
                id_vehiculo,
                comando=estado["comando"] if estado else None,
                codigo=estado["codigo"] if estado else None,
                estado=jsonable_encoder(estado),
            ),
        )

        # Mantiene la conexión abierta y detecta desconexiones.
        while True:
            await websocket.receive_text()

    except (WebSocketDisconnect, WebSocketDisconnected):
        # El cliente se desconecto o la conexion dejo
        # de estar disponible.
        pass

    finally:
        manager.desconectar(id_vehiculo, websocket)
