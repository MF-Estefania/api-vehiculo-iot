import asyncio

from fastapi import APIRouter, Path

from app.exceptions import ConflictoError
from app.models.movimiento import MovimientoCrear, MovimientoOut
from app.services.demo_runner import runner
from app.services.movimiento_service import MovimientoService
from app.websocket.eventos import crear_evento
from app.websocket.manager import manager

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/movimientos", tags=["Movimientos"])
servicio = MovimientoService()


@router.post(
    "",
    response_model=MovimientoOut,
    status_code=201,
    summary="Registrar un movimiento individual",
    description=(
        "Ejecuta un comando **existente** del catálogo del vehículo: actualiza el último "
        "estado y registra el movimiento en el historial dentro de **una sola transacción**. "
        "Después de confirmar en RDS, notifica por WebSocket a los clientes que monitorean "
        "ese vehículo. No crea comandos nuevos. Se rechaza mientras el vehículo ejecuta una DEMO. "
        "**SP:** `sp_obtener_vehiculo`, `sp_obtener_comandos_vehiculo`, `sp_obtener_estado`, "
        "`sp_actualizar_estado` y `sp_registrar_historial`."
    ),
    responses={
        404: {"description": "El vehículo no existe o el comando no es de ese vehículo"},
        409: {
            "description": "El vehículo o el comando están inactivos, "
            "o hay una DEMO en ejecución"
        },
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
async def registrar_movimiento(
    datos: MovimientoCrear,
    id_vehiculo: int = Path(..., gt=0, description="ID del vehículo"),
):
    # Un movimiento individual no debe mezclarse con una DEMO en curso.
    if runner.activa(id_vehiculo):
        raise ConflictoError("Hay una DEMO en ejecución para este vehículo")

    # El trabajo bloqueante con RDS corre en un hilo para no congelar el servidor.
    resultado = await asyncio.to_thread(servicio.registrar, id_vehiculo, datos)

    # Solo se llega aquí si la transacción se confirmó; un rechazo no emite evento.
    evento = crear_evento(
        "movimiento_individual",
        id_vehiculo,
        comando=resultado["comando"],
        codigo=resultado["codigo"],
        origen=resultado["origen"],
    )
    notificados = await manager.difundir(id_vehiculo, evento)
    return {**resultado, "clientes_notificados": notificados}