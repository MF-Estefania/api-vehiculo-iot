from fastapi import APIRouter, Depends, Path

from app.models.comun import MensajeOut
from app.models.demo import (
    DemoActualizar,
    DemoCrear,
    DemoIniciadaOut,
    DemoOut,
    MovimientoDemoActualizar,
    MovimientoDemoCrear,
    MovimientoDemoOut,
)
from app.security import requerir_api_key
from app.services.demo_runner import runner
from app.services.demo_service import DemoService

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/demos", tags=["DEMO"])
servicio = DemoService()

_ID_VEHICULO = Path(..., gt=0, description="ID del vehículo")
_ID_DEMO = Path(..., gt=0, description="ID de la DEMO")
_ID_MOVIMIENTO = Path(..., gt=0, description="ID del movimiento de la DEMO")

_R_NOT_FOUND = {404: {"description": "El vehículo no existe o la DEMO/comando no es de ese vehículo"}}
_R_DB = {503: {"description": "Base de datos no disponible"}}
_R_AUTH = {
    401: {"description": "Falta la clave de API"},
    403: {"description": "Clave de API inválida"},
}


# --- Consultas ----------------------------------------------------------


@router.get(
    "",
    response_model=list[DemoOut],
    summary="Listar las DEMO de un vehículo",
    description=(
        "Devuelve las DEMO del vehículo (una lista vacía es una consulta válida). "
        "**SP:** `sp_obtener_vehiculo` y `sp_obtener_demos`."
    ),
    responses={**_R_NOT_FOUND, **_R_DB},
)
def listar_demos(id_vehiculo: int = _ID_VEHICULO):
    return servicio.listar(id_vehiculo)


@router.get(
    "/{id_demo}/movimientos",
    response_model=list[MovimientoDemoOut],
    summary="Consultar los movimientos de una DEMO",
    description=(
        "Devuelve los N movimientos de la DEMO en su orden, con duración y pausa. "
        "No modifica datos. **SP:** `sp_obtener_demos` y `sp_obtener_movimientos_demo`."
    ),
    responses={**_R_NOT_FOUND, **_R_DB},
)
def listar_movimientos_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return servicio.listar_movimientos(id_vehiculo, id_demo)


# --- Administración de DEMO ---------------------------------------------


@router.post(
    "",
    response_model=DemoOut,
    status_code=201,
    summary="Crear una DEMO",
    description="Crea una DEMO vacía para el vehículo. **SP:** `sp_obtener_vehiculo`, `sp_crear_demo` y `sp_obtener_demos`.",
    responses={**_R_NOT_FOUND, 422: {"description": "Datos inválidos"}, **_R_DB},
)
def crear_demo(datos: DemoCrear, id_vehiculo: int = _ID_VEHICULO):
    return servicio.crear(id_vehiculo, datos)


@router.post(
    "/{id_demo}/actualizar",
    response_model=DemoOut,
    summary="Actualizar una DEMO",
    description="Reemplaza nombre, descripción y estado activo. **SP:** `sp_obtener_demos` y `sp_actualizar_demo`.",
    responses={**_R_NOT_FOUND, 422: {"description": "Datos inválidos"}, **_R_DB},
)
def actualizar_demo(
    datos: DemoActualizar, id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO
):
    return servicio.actualizar(id_vehiculo, id_demo, datos)


@router.post(
    "/{id_demo}/eliminar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_api_key)],
    summary="Eliminar una DEMO (protegido)",
    description="Elimina una DEMO. Requiere `X-API-Key`. **SP:** `sp_obtener_demos` y `sp_eliminar_demo`.",
    responses={
        **_R_AUTH,
        **_R_NOT_FOUND,
        409: {"description": "La DEMO todavía tiene movimientos"},
        **_R_DB,
    },
)
def eliminar_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    servicio.eliminar(id_vehiculo, id_demo)
    return MensajeOut(mensaje=f"DEMO {id_demo} eliminada")


# --- Movimientos de la DEMO ---------------------------------------------


@router.post(
    "/{id_demo}/movimientos",
    response_model=list[MovimientoDemoOut],
    status_code=201,
    summary="Agregar un movimiento a una DEMO",
    description=(
        "Agrega un movimiento (comando, orden, duración y pausa) y devuelve la secuencia "
        "actualizada. El comando debe ser del mismo vehículo. "
        "**SP:** `sp_obtener_demos`, `sp_obtener_comandos_vehiculo`, "
        "`sp_agregar_movimiento_demo` y `sp_obtener_movimientos_demo`."
    ),
    responses={
        **_R_NOT_FOUND,
        409: {"description": "Ya existe un movimiento con ese orden"},
        422: {"description": "Datos inválidos"},
        **_R_DB,
    },
)
def agregar_movimiento(
    datos: MovimientoDemoCrear, id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO
):
    return servicio.agregar_movimiento(id_vehiculo, id_demo, datos)


@router.post(
    "/{id_demo}/movimientos/{id_movimiento}/actualizar",
    response_model=MovimientoDemoOut,
    summary="Actualizar un movimiento de una DEMO",
    description=(
        "Reemplaza comando, orden, duración y pausa del movimiento. "
        "**SP:** `sp_obtener_movimientos_demo` y `sp_actualizar_movimiento_demo`."
    ),
    responses={
        **_R_NOT_FOUND,
        409: {"description": "Ya existe un movimiento con ese orden"},
        422: {"description": "Datos inválidos"},
        **_R_DB,
    },
)
def actualizar_movimiento(
    datos: MovimientoDemoActualizar,
    id_vehiculo: int = _ID_VEHICULO,
    id_demo: int = _ID_DEMO,
    id_movimiento: int = _ID_MOVIMIENTO,
):
    return servicio.actualizar_movimiento(id_vehiculo, id_demo, id_movimiento, datos)


@router.post(
    "/{id_demo}/movimientos/{id_movimiento}/eliminar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_api_key)],
    summary="Eliminar un movimiento de una DEMO (protegido)",
    description=(
        "Elimina un movimiento. Requiere `X-API-Key`. "
        "**SP:** `sp_obtener_movimientos_demo` y `sp_eliminar_movimiento_demo`."
    ),
    responses={**_R_AUTH, **_R_NOT_FOUND, **_R_DB},
)
def eliminar_movimiento(
    id_vehiculo: int = _ID_VEHICULO,
    id_demo: int = _ID_DEMO,
    id_movimiento: int = _ID_MOVIMIENTO,
):
    servicio.eliminar_movimiento(id_vehiculo, id_demo, id_movimiento)
    return MensajeOut(mensaje=f"Movimiento {id_movimiento} eliminado")


# --- Ejecución ------------------------------------------------------------


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
    responses={**_R_AUTH, 409: {"description": "No hay una DEMO en ejecución"}},
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
        **_R_AUTH,
        **_R_NOT_FOUND,
        409: {"description": "Ya hay una DEMO en ejecución, o el vehículo/DEMO están inactivos, o la DEMO no tiene movimientos"},
        **_R_DB,
    },
)
async def iniciar_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return await runner.iniciar(id_vehiculo, id_demo)