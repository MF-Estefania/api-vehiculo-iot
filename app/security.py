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