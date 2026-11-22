import asyncio

from fastapi import APIRouter, Depends, Path

from app.exceptions import ConflictoError
from app.models.movimiento import MovimientoCrear, MovimientoOut
from app.services.demo_runner import runner
from app.services.control_concurrencia import control_concurrencia
from app.services.movimiento_service import MovimientoService
from app.websocket.eventos import crear_evento
from app.websocket.manager import manager
from app.security import autorizar_operacion_vehiculo

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/movimientos", tags=["Movimientos"])
servicio = MovimientoService()
router_stop = APIRouter(tags=["Control del vehículo"])


@router.post(
    "",
    response_model=MovimientoOut,
    dependencies=[Depends(autorizar_operacion_vehiculo)],
    status_code=201,
    summary="Registrar un movimiento individual",
    description=(
        "Ejecuta un comando del catálogo del vehículo: actualiza el último "
        "estado y registra el movimiento en el historial dentro de una transacción. "
        "Autorizado por rol y propiedad/reserva (BOLA protegido)."
    ),
    responses={
        401: {"description": "No autenticado o token expirado"},
        403: {"description": "Vehículo ajeno o demo temporal expirada"},
        404: {"description": "El vehículo no existe o el comando no es de ese vehículo"},
        409: {"description": "Vehículo o comando inactivo, o DEMO en ejecución"},
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
async def registrar_movimiento(
    datos: MovimientoCrear,
    id_vehiculo: int = Path(..., gt=0, description="ID del vehículo"),
):
    if runner.activa(id_vehiculo):
        raise ConflictoError("Hay una DEMO en ejecución para este vehículo")

    generacion_inicial = control_concurrencia.generacion(id_vehiculo)
    resultado = await asyncio.to_thread(servicio.registrar, id_vehiculo, datos)

    async with control_concurrencia.bloqueo(id_vehiculo):
        if control_concurrencia.generacion(id_vehiculo) != generacion_inicial:
            return {**resultado, "clientes_notificados": 0}

        if runner.activa(id_vehiculo):
            return {**resultado, "clientes_notificados": 0}

        evento = crear_evento(
            "movimiento_individual",
            id_vehiculo,
            comando=resultado["comando"],
            codigo=resultado["codigo"],
            origen=resultado["origen"],
        )
        notificados = await manager.difundir(id_vehiculo, evento)

    return {**resultado, "clientes_notificados": notificados}


@router_stop.post(
    "/vehiculos/{id_vehiculo}/detener",
    dependencies=[Depends(autorizar_operacion_vehiculo)],
    summary="Solicitar detención remota del vehículo",
)
async def detener_vehiculo(
    id_vehiculo: int = Path(..., gt=0),
):
    control_concurrencia.invalidar_pendientes(id_vehiculo)

    if runner.activa(id_vehiculo):
        runner.cancelar(id_vehiculo)

    async with control_concurrencia.bloqueo(id_vehiculo):
        evento = crear_evento(
            "detener_vehiculo",
            id_vehiculo,
            codigo="0",
            origen="scarlette_web",
        )
        notificados = await manager.difundir(id_vehiculo, evento)

    return {
        "mensaje": "Solicitud de detención enviada",
        "id_vehiculo": id_vehiculo,
        "clientes_notificados": notificados,
    }
