from fastapi import APIRouter, Depends, Path

from app.models.comun import MensajeOut
from app.models.demo import DemoIniciadaOut, DemoOut, MovimientoDemoOut
from app.security import requerir_api_key
from app.services.demo_runner import runner
from app.services.demo_service import DemoService

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/demos", tags=["DEMO"])
servicio = DemoService()

_ID_VEHICULO = Path(..., gt=0, description="ID del vehículo")
_ID_DEMO = Path(..., gt=0, description="ID de la DEMO")


@router.get(
    "",
    response_model=list[DemoOut],
    summary="Listar las DEMO de un vehículo",
    description=(
        "Devuelve las DEMO asociadas al vehículo (una lista vacía es una consulta válida). "
        "**SP:** `sp_obtener_vehiculo` y `sp_obtener_demos`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        503: {"description": "Base de datos no disponible"},
    },
)
def listar_demos(id_vehiculo: int = _ID_VEHICULO):
    return servicio.listar(id_vehiculo)


@router.get(
    "/{id_demo}/movimientos",
    response_model=list[MovimientoDemoOut],
    summary="Consultar los movimientos de una DEMO",
    description=(
        "Devuelve los N movimientos de la DEMO en su orden, con duración y pausa. "
        "No modifica datos. "
        "**SP:** `sp_obtener_demos` y `sp_obtener_movimientos_demo`."
    ),
    responses={
        404: {"description": "El vehículo no existe o la DEMO no es de ese vehículo"},
        503: {"description": "Base de datos no disponible"},
    },
)
def listar_movimientos_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return servicio.listar_movimientos(id_vehiculo, id_demo)


@router.post(
    "/cancelar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_api_key)],
    summary="Cancelar la DEMO en ejecución (protegido)",
    description=(
        "Detiene de inmediato la DEMO activa del vehículo: no se emite ningún movimiento "
        "posterior y se envía el evento `demo_cancelada` por WebSocket. Requiere "
        "`X-API-Key`. No usa Stored Procedures."
    ),
    responses={
        401: {"description": "Falta la clave de API"},
        403: {"description": "Clave de API inválida"},
        409: {"description": "No hay una DEMO en ejecución"},
    },
)
def cancelar_demo(id_vehiculo: int = _ID_VEHICULO):
    runner.cancelar(id_vehiculo)
    return MensajeOut(mensaje="Cancelación solicitada")


@router.post(
    "/{id_demo}/iniciar",
    response_model=DemoIniciadaOut,
    status_code=202,
    dependencies=[Depends(requerir_api_key)],
    summary="Iniciar una DEMO (protegido)",
    description=(
        "Valida que el vehículo y la DEMO existan, estén activos y se pertenezcan; "
        "responde de inmediato (202) y transmite los N movimientos por WebSocket, "
        "respetando duración y pausa. Actualiza el estado y **no** registra historial. "
        "Solo una DEMO por vehículo a la vez. Requiere `X-API-Key`. "
        "**SP:** `sp_obtener_vehiculo`, `sp_obtener_demos`, `sp_obtener_movimientos_demo`, "
        "`sp_obtener_estado` y `sp_actualizar_estado`."
    ),
    responses={
        401: {"description": "Falta la clave de API"},
        403: {"description": "Clave de API inválida"},
        404: {"description": "El vehículo no existe o la DEMO no es de ese vehículo"},
        409: {"description": "Ya hay una DEMO en ejecución, o el vehículo/DEMO están inactivos, o la DEMO no tiene movimientos"},
        503: {"description": "Base de datos no disponible"},
    },
)
async def iniciar_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return await runner.iniciar(id_vehiculo, id_demo)