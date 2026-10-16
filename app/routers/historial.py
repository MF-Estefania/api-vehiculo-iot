from fastapi import APIRouter, Path

from app.models.historial import HistorialOut
from app.services.historial_service import HistorialService

router = APIRouter(prefix="/vehiculos/{id_vehiculo}/historial", tags=["Historial"])
servicio = HistorialService()


@router.get(
    "",
    response_model=list[HistorialOut],
    summary="Consultar los últimos movimientos individuales",
    description=(
        "Devuelve **como máximo los 10 movimientos individuales más recientes**, del más "
        "reciente al más antiguo. Si hay menos, devuelve solo los disponibles; los "
        "movimientos de DEMO nunca aparecen aquí. No modifica datos. "
        "**SP:** `sp_obtener_vehiculo` y `sp_obtener_historial`."
    ),
    responses={
        404: {"description": "El vehículo no existe"},
        503: {"description": "Base de datos no disponible"},
    },
)
def obtener_historial(id_vehiculo: int = Path(..., gt=0, description="ID del vehículo")):
    return servicio.ultimos(id_vehiculo)