import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.database import DatabaseError
from app.exceptions import RecursoNoEncontrado
from app.services.estado_service import EstadoService
from app.websocket.eventos import crear_evento
from app.websocket.manager import manager

router = APIRouter()
estados = EstadoService()


@router.websocket("/ws/vehiculos/{id_vehiculo}")
async def monitorear_vehiculo(websocket: WebSocket, id_vehiculo: int):
    """Monitoreo en tiempo real de un vehículo.

    Al conectar envía el último estado; después recibe los eventos del vehículo.
    """
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

        # Mantiene la conexión abierta y detecta cuándo el cliente se desconecta.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.desconectar(id_vehiculo, websocket)