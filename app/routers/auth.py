from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.services.auth_service import AuthService
from app.services.login_attempt_service import LoginAttemptService
from app.services.ws_ticket_service import WsTicketService

router = APIRouter(prefix="/auth", tags=["Autenticación"])

servicio = AuthService()
esquema_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    nombre_usuario: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


def obtener_token(
    credenciales: HTTPAuthorizationCredentials | None = Depends(
        esquema_bearer
    ),
):
    if credenciales is None:
        raise HTTPException(
            status_code=401,
            detail="Se requiere iniciar sesión",
        )

    return credenciales.credentials


@router.post("/login")
def login(datos: LoginRequest):
    proteccion = LoginAttemptService()

    if proteccion.esta_bloqueado(datos.nombre_usuario):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Intenta nuevamente más tarde.",
        )

    resultado = servicio.iniciar_sesion(
        datos.nombre_usuario,
        datos.password,
    )

    if resultado is None:
        proteccion.registrar_fallo(datos.nombre_usuario)
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
        )

    proteccion.limpiar_intentos(datos.nombre_usuario)
    return resultado


@router.get("/me")
def mi_cuenta(token: str = Depends(obtener_token)):
    usuario = servicio.verificar_sesion(token)

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada",
        )

    return usuario


@router.post("/logout")
def logout(token: str = Depends(obtener_token)):
    usuario = servicio.verificar_sesion(token)

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada",
        )

    servicio.cerrar_sesion(token)

    return {"mensaje": "Sesión cerrada correctamente"}

@router.post("/ws-ticket")
def solicitar_ticket_ws(token: str = Depends(obtener_token)):
    usuario = servicio.verificar_sesion(token)

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada",
        )

    ticket_service = WsTicketService()

    return ticket_service.crear_ticket(
        id_usuario=usuario["id_usuario"],
        id_vehiculo=7,
    )
