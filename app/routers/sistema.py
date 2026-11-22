from datetime import datetime, timezone
from fastapi import APIRouter

from app.database import db

router = APIRouter(prefix="/sistema", tags=["Diagnóstico y Salud"])


@router.get("/salud")
def verificar_salud():
    """Diagnóstico independiente de salud de la API AWS y verificación real de Amazon RDS MySQL."""
    rds_ok = False
    try:
        rds_ok = db.ping()
    except Exception:
        rds_ok = False

    return {
        "api_status": "disponible",
        "rds_status": "disponible" if rds_ok else "no disponible",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
