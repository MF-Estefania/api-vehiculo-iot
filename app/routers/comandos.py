from fastapi import APIRouter, Depends, Path

from app.models.comando import ComandoActualizar, ComandoCrear, ComandoOut
from app.models.comun import MensajeOut
from app.security import requerir_api_key
from app.services.comando_service import ComandoService

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/comandos", tags=["Comandos"])
servicio = ComandoService()

_ID_VEHICULO = Path(..., gt=0, description="ID del vehículo")
_ID_COMANDO = Path(..., gt=0, description="ID del comando")


@router.get(
    "",
    response_model=list[ComandoOut],
    summary="Listar comandos de un vehículo",
    description=(
        "Catálogo de comandos del vehículo (una lista vacía es una consulta válida). "
        "**SP:** `sp_obtener_vehiculo` y `sp_obtener_comandos_vehiculo`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        503: {"description": "Base de datos no disponible"},
    },
)
def listar_comandos(id_vehiculo: int = _ID_VEHICULO):
    return servicio.listar(id_vehiculo)


@router.post(
    "",
    response_model=ComandoOut,
    status_code=201,
    summary="Crear un comando en el catálogo",
    description=(
        "Agrega un comando nuevo al catálogo del vehículo (no ejecuta ningún movimiento). "
        "**SP:** `sp_obtener_vehiculo`, `sp_crear_comando` y `sp_obtener_comandos_vehiculo`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        409: {"description": "Nombre o código repetido"},
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
def crear_comando(datos: ComandoCrear, id_vehiculo: int = _ID_VEHICULO):
    return servicio.crear(id_vehiculo, datos)


@router.post(
    "/{id_comando}/actualizar",
    response_model=ComandoOut,
    summary="Actualizar un comando",
    description=(
        "Reemplaza los datos de un comando del vehículo (todos los campos son obligatorios). "
        "**SP:** `sp_obtener_comandos_vehiculo` y `sp_actualizar_comando`."
    ),
    responses={
        404: {"description": "El vehículo no existe o el comando no es de ese vehículo"},
        409: {"description": "Nombre o código repetido"},
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
def actualizar_comando(
    datos: ComandoActualizar,
    id_vehiculo: int = _ID_VEHICULO,
    id_comando: int = _ID_COMANDO,
):
    return servicio.actualizar(id_vehiculo, id_comando, datos)


@router.post(
    "/{id_comando}/eliminar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_api_key)],
    summary="Eliminar un comando (protegido)",
    description=(
        "Elimina un comando del catálogo. Requiere el encabezado `X-API-Key`. "
        "**SP:** `sp_obtener_comandos_vehiculo` y `sp_eliminar_comando`."
    ),
    responses={
        401: {"description": "Falta la clave de API"},
        403: {"description": "Clave de API inválida"},
        404: {"description": "El vehículo no existe o el comando no es de ese vehículo"},
        409: {"description": "El comando se usa en una DEMO o en el historial"},
        503: {"description": "Base de datos no disponible"},
    },
)
def eliminar_comando(id_vehiculo: int = _ID_VEHICULO, id_comando: int = _ID_COMANDO):
    servicio.eliminar(id_vehiculo, id_comando)
    return MensajeOut(mensaje=f"Comando {id_comando} eliminado")