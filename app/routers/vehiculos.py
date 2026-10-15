from fastapi import APIRouter, Path

from app.models.vehiculo import VehiculoOut
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