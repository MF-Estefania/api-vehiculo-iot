import secrets
from fastapi import Depends, Header, HTTPException, Path, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.services.auth_service import AuthService
from app.services.mis_vehiculos_service import MisVehiculosService
from app.services.invitado_service import InvitadoService

_esquema = APIKeyHeader(name="X-API-Key", auto_error=False)
_esquema_bearer = HTTPBearer(auto_error=False)
_auth_service = AuthService()
_mis_vehiculos_service = MisVehiculosService()
_invitado_service = InvitadoService()


def requerir_api_key(clave: str | None = Security(_esquema)) -> None:
    if not clave:
        raise HTTPException(status_code=401, detail="Falta la clave de API (X-API-Key)")
    if not secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        raise HTTPException(status_code=403, detail="Clave de API inválida")


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> dict | None:
    if credenciales is None:
        return None
    return _auth_service.verificar_sesion(credenciales.credentials)


def requerir_usuario_autenticado(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> dict:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Se requiere iniciar sesión")
    usuario = _auth_service.verificar_sesion(credenciales.credentials)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    return usuario


def requerir_api_key_o_sesion(
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> dict:
    if clave and secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        return {"id_usuario": 0, "nombre_usuario": "sistema_api_key", "rol": "administrador"}

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(credenciales.credentials)
        if usuario is not None and usuario["rol"] in ("administradora", "administrador", "usuario", "invitado"):
            return usuario

    raise HTTPException(status_code=401, detail="API Key o sesión válida requerida")


def requerir_administradora(
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> dict:
    if clave and secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        return {"id_usuario": 1, "nombre_usuario": "administrador_api", "rol": "administrador"}

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(credenciales.credentials)
        if usuario is not None and usuario["rol"] in ("administradora", "administrador"):
            return usuario

    raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")


def requerir_admin_o_propietario(
    id_vehiculo: int = Path(..., gt=0),
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> dict:
    if clave and secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        return {"id_usuario": 1, "nombre_usuario": "administrador_api", "rol": "administrador"}

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(credenciales.credentials)
        if usuario:
            rol = usuario["rol"]
            if rol in ("administradora", "administrador"):
                return usuario
            if rol == "usuario" and _mis_vehiculos_service.verificar_propiedad(usuario["id_usuario"], rol, id_vehiculo):
                return usuario
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado: no tienes permisos para gestionar este vehículo {id_vehiculo}",
            )

    raise HTTPException(status_code=401, detail="Sesión válida requerida")


def autorizar_operacion_vehiculo(
    id_vehiculo: int = Path(..., gt=0),
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    token_invitado: str | None = Header(None, alias="X-Guest-Token"),
) -> dict:
    if clave and secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        return {"id_usuario": 0, "nombre_usuario": "sistema_api_key", "rol": "administrador"}

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(credenciales.credentials)
        if usuario:
            rol = usuario["rol"]
            if rol in ("administradora", "administrador"):
                return usuario
            if rol == "usuario":
                if _mis_vehiculos_service.verificar_propiedad(usuario["id_usuario"], rol, id_vehiculo):
                    return usuario
                raise HTTPException(
                    status_code=403,
                    detail=f"Acceso denegado: el vehículo {id_vehiculo} no pertenece a tu cuenta",
                )
            if rol == "invitado":
                if _invitado_service.verificar_reserva_activa(id_vehiculo, token_invitado):
                    return usuario
                raise HTTPException(
                    status_code=403,
                    detail="Sesión de demostración temporal no válida o expirada",
                )

    if token_invitado:
        if _invitado_service.verificar_reserva_activa(id_vehiculo, token_invitado):
            return {"id_usuario": 3, "nombre_usuario": "invitado_demo", "rol": "invitado"}

    raise HTTPException(status_code=401, detail="Autorización requerida para operar este vehículo")
