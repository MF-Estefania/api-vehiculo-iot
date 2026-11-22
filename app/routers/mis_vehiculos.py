from fastapi import APIRouter, Depends

from app.security import requerir_usuario_autenticado
from app.services.mis_vehiculos_service import MisVehiculosService

router = APIRouter(prefix="/mis-vehiculos", tags=["Mis Vehículos (Comprador)"])
mis_vehiculos_service = MisVehiculosService()


@router.get("")
def obtener_mis_vehiculos(usuario: dict = Depends(requerir_usuario_autenticado)):
    """Devuelve las unidades físicas asignadas al cliente autenticado."""
    return mis_vehiculos_service.listar_por_usuario(
        id_usuario=usuario["id_usuario"],
        rol=usuario["rol"],
    )
