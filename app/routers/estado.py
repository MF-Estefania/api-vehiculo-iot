from fastapi import APIRouter, Path

from app.models.estado import EstadoOut
from app.services.estado_service import EstadoService

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/estado", tags=["Estado"])
servicio = EstadoService()


@router.get(
    "",
    response_model=EstadoOut | None,
    summary="Consultar el último estado de un vehículo",
    description=(
        "Devuelve el último estado registrado, o `null` si el vehículo aún no tiene "
        "ninguno (consulta válida). No modifica datos. "
        "**SP:** `sp_obtener_vehiculo` y `sp_obtener_estado`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        503: {"description": "Base de datos no disponible"},
    },
)
def obtener_estado(id_vehiculo: int = Path(..., gt=0, description="ID del vehículo")):
    return servicio.obtener(id_vehiculo)