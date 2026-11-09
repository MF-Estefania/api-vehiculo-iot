import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_esquema = APIKeyHeader(name="X-API-Key", auto_error=False)


def requerir_api_key(clave: str | None = Security(_esquema)) -> None:
    """Dependencia que protege operaciones de control y eliminación.

    401 si falta la clave, 403 si es incorrecta.
    """
    if not clave:
        raise HTTPException(status_code=401, detail="Falta la clave de API (X-API-Key)")
    if not secrets.compare_digest(clave.encode(), settings.api_key.encode()):
        raise HTTPException(status_code=403, detail="Clave de API inválida")


from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import AuthService


_esquema_bearer = HTTPBearer(auto_error=False)
_auth_service = AuthService()


def requerir_api_key_o_sesion(
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> None:
    """Autoriza mediante API Key o sesión válida de SCARLETTE."""

    if clave and secrets.compare_digest(
        clave.encode(), settings.api_key.encode()
    ):
        return

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(
            credenciales.credentials
        )

        if usuario is not None and usuario["rol"] in (
            "administradora",
            "usuario",
        ):
            return

    raise HTTPException(
        status_code=401,
        detail="API Key o sesión válida requerida",
    )

def requerir_administradora(
    clave: str | None = Security(_esquema),
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> None:
    """Permite la API Key original o una sesión administradora."""

    if clave and secrets.compare_digest(
        clave.encode(), settings.api_key.encode()
    ):
        return

    if credenciales is not None:
        usuario = _auth_service.verificar_sesion(
            credenciales.credentials
        )

        if usuario is not None and usuario["rol"] == "administradora":
            return

    raise HTTPException(
        status_code=403,
        detail="Se requieren permisos de administradora",
    )
