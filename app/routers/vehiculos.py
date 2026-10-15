from fastapi import APIRouter, Depends, Path

from app.models.comun import MensajeOut
from app.models.vehiculo import VehiculoActualizar, VehiculoCrear, VehiculoOut
from app.security import requerir_api_key
from app.services.vehiculo_service import VehiculoService

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])
servicio = VehiculoService()


@router.get(
    "",
    response_model=list[VehiculoOut],
    summary="Listar vehículos",
    description="Devuelve todos los vehículos registrados. **SP:** `sp_obtener_vehiculos`.",
    responses={503: {"description": "Base de datos no disponible"}},
)
def listar_vehiculos():
    return servicio.listar()


@router.get(
    "/{id_vehiculo}",
    response_model=VehiculoOut,
    summary="Obtener un vehículo",
    description="Devuelve un vehículo por su identificador. **SP:** `sp_obtener_vehiculo`.",
    responses={
        404: {"description": "El vehículo no existe"},
        422: {"description": "Identificador inválido"},
        503: {"description": "Base de datos no disponible"},
    },
)
def obtener_vehiculo(id_vehiculo: int = Path(..., gt=0, description="ID del vehículo")):
    return servicio.obtener(id_vehiculo)


@router.post(
    "",
    response_model=VehiculoOut,
    status_code=201,
    summary="Registrar un vehículo",
    description=(
        "Crea un vehículo y lo devuelve. "
        "**SP:** `sp_crear_vehiculo` y `sp_obtener_vehiculo`."
    ),
    responses={
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
def crear_vehiculo(datos: VehiculoCrear):
    return servicio.crear(datos)


@router.post(
    "/{id_vehiculo}/actualizar",
    response_model=VehiculoOut,
    summary="Actualizar un vehículo",
    description=(
        "Reemplaza los datos del vehículo (todos los campos son obligatorios). "
        "**SP:** `sp_obtener_vehiculo` y `sp_actualizar_vehiculo`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        422: {"description": "Datos inválidos"},
        503: {"description": "Base de datos no disponible"},
    },
)
def actualizar_vehiculo(
    datos: VehiculoActualizar,
    id_vehiculo: int = Path(..., gt=0, description="ID del vehículo"),
):
    return servicio.actualizar(id_vehiculo, datos)


@router.post(
    "/{id_vehiculo}/eliminar",
    response_model=MensajeOut,
    dependencies=[Depends(requerir_api_key)],
    summary="Eliminar un vehículo (protegido)",
    description=(
        "Elimina un vehículo. Requiere el encabezado `X-API-Key`. "
        "**SP:** `sp_obtener_vehiculo` y `sp_eliminar_vehiculo`."
    ),
    responses={
        401: {"description": "Falta la clave de API"},
        403: {"description": "Clave de API inválida"},
        404: {"description": "El vehículo no existe"},
        409: {"description": "El vehículo tiene datos relacionados"},
        503: {"description": "Base de datos no disponible"},
    },
)
def eliminar_vehiculo(id_vehiculo: int = Path(..., gt=0, description="ID del vehículo")):
    servicio.eliminar(id_vehiculo)
    return MensajeOut(mensaje=f"Vehículo {id_vehiculo} eliminado")