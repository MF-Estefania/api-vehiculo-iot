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
from app.security import (
    autorizar_operacion_vehiculo,
    requerir_admin_o_propietario,
    requerir_administradora,
)
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
    401: {"description": "Falta la clave de API o sesión"},
    403: {"description": "Permisos insuficientes"},
}


# --- Consultas ----------------------------------------------------------


@router.get(
    "",
    response_model=list[DemoOut],
    summary="Listar las DEMO de un vehículo",
    description="Devuelve las DEMO del vehículo. **SP:** `sp_obtener_vehiculo` y `sp_obtener_demos`.",
    responses={**_R_NOT_FOUND, **_R_DB},
)
def listar_demos(id_vehiculo: int = _ID_VEHICULO):
    return servicio.listar(id_vehiculo)


@router.get(
    "/{id_demo}/movimientos",
    response_model=list[MovimientoDemoOut],
    summary="Consultar los movimientos de una DEMO",
    description="Devuelve los movimientos de la DEMO en orden. **SP:** `sp_obtener_demos` y `sp_obtener_movimientos_demo`.",
    responses={**_R_NOT_FOUND, **_R_DB},
)
def listar_movimientos_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return servicio.listar_movimientos(id_vehiculo, id_demo)


# --- Administración y Edición de DEMO (Admin o Comprador) ----------------


@router.post(
    "",
    response_model=DemoOut,
    status_code=201,
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Crear una DEMO (Fábrica o Privada)",
    description="Crea una DEMO para el vehículo asignado o como administrador. **SP:** `sp_crear_demo`.",
    responses={**_R_NOT_FOUND, 422: {"description": "Datos inválidos"}, **_R_DB},
)
def crear_demo(datos: DemoCrear, id_vehiculo: int = _ID_VEHICULO):
    return servicio.crear(id_vehiculo, datos)


@router.post(
    "/{id_demo}/actualizar",
    response_model=DemoOut,
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Actualizar una DEMO",
    description="Actualiza nombre, descripción y estado activo. **SP:** `sp_actualizar_demo`.",
    responses={**_R_NOT_FOUND, 422: {"description": "Datos inválidos"}, **_R_DB},
)
def actualizar_demo(
    datos: DemoActualizar, id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO
):
    return servicio.actualizar(id_vehiculo, id_demo, datos)


@router.post(
    "/{id_demo}/eliminar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Eliminar una DEMO",
    description="Elimina una DEMO sin movimientos. **SP:** `sp_eliminar_demo`.",
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
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Agregar un movimiento a una DEMO",
    description="Agrega un movimiento y devuelve la secuencia. **SP:** `sp_agregar_movimiento_demo`.",
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
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Actualizar un movimiento de una DEMO",
    description="Reemplaza orden, duración y pausa del movimiento.",
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
    dependencies=[Depends(requerir_admin_o_propietario)],
    summary="Eliminar un movimiento de una DEMO",
    description="Elimina un movimiento de la DEMO. **SP:** `sp_eliminar_movimiento_demo`.",
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
    dependencies=[Depends(autorizar_operacion_vehiculo)],
    summary="Cancelar la DEMO en ejecución",
)
def cancelar_demo(id_vehiculo: int = _ID_VEHICULO):
    runner.cancelar(id_vehiculo)
    return MensajeOut(mensaje="Cancelación solicitada")


@router.post(
    "/{id_demo}/iniciar",
    response_model=DemoIniciadaOut,
    status_code=202,
    dependencies=[Depends(autorizar_operacion_vehiculo)],
    summary="Iniciar una DEMO autorizada",
)
async def iniciar_demo(id_vehiculo: int = _ID_VEHICULO, id_demo: int = _ID_DEMO):
    return await runner.iniciar(id_vehiculo, id_demo)
