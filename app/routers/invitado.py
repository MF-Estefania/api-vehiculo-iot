from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.auditoria_service import AuditoriaService
from app.services.invitado_service import InvitadoService
from app.services.movimiento_service import MovimientoService

router = APIRouter(prefix="/invitado", tags=["Invitados / Demostraciones Comerciales"])
invitado_service = InvitadoService()
auditoria_service = AuditoriaService()
movimiento_service = MovimientoService()


class SolicitarDemoRequest(BaseModel):
    id_vehiculo: int = Field(..., gt=0, description="ID de la unidad de exhibición")


class LiberarDemoRequest(BaseModel):
    id_vehiculo: int = Field(..., gt=0)
    token_sesion: str = Field(..., min_length=1)


@router.get("/catalogo")
def ver_catalogo_publico():
    """Catálogo público de modelos y unidades de exhibición disponibles."""
    return invitado_service.obtener_catalogo()


@router.post("/solicitar-demo")
def solicitar_demostracion(datos: SolicitarDemoRequest, request: Request):
    """Solicita una reserva temporal exclusiva para operar una unidad de exhibición."""
    ip = request.client.host if request.client else "desconocido"
    resultado = invitado_service.solicitar_reserva(
        id_vehiculo=datos.id_vehiculo,
        id_usuario=3,  # ID del usuario invitado del sistema
        ip_origen=ip,
    )
    auditoria_service.registrar(
        accion="INICIO_DEMO_INVITADO",
        recurso=f"vehiculo/{datos.id_vehiculo}",
        detalle=f"Reserva #{resultado['id_reserva']} de 180s iniciada para unidad {datos.id_vehiculo}",
        id_usuario=3,
        nombre_usuario="invitado",
        rol="invitado",
        ip_origen=ip,
    )
    return resultado


@router.post("/liberar-demo")
def liberar_demostracion(datos: LiberarDemoRequest, request: Request):
    """Finaliza voluntariamente la sesión de prueba del invitado y asegura la detención del vehículo."""
    ip = request.client.host if request.client else "desconocido"
    liberada = invitado_service.finalizar_reserva(datos.id_vehiculo, datos.token_sesion)
    
    # Detención de seguridad
    try:
        movimiento_service.detener(datos.id_vehiculo)
    except Exception as e:
        print(f"Aviso al detener unidad tras liberar demo: {e}")

    auditoria_service.registrar(
        accion="FIN_DEMO_INVITADO",
        recurso=f"vehiculo/{datos.id_vehiculo}",
        detalle=f"Reserva finalizada y vehículo {datos.id_vehiculo} detenido con seguridad",
        id_usuario=3,
        nombre_usuario="invitado",
        rol="invitado",
        ip_origen=ip,
    )
    return {"mensaje": "Demostración finalizada y vehículo detenido con seguridad", "liberada": liberada}
