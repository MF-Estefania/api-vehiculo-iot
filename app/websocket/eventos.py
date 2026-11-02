
from datetime import datetime, timezone


def crear_evento(
    tipo: str,
    id_vehiculo: int,
    comando: str | None = None,
    codigo: str | None = None,
    **extra,
) -> dict:
    return {
        "tipo": tipo,
        "id_vehiculo": id_vehiculo,
        "comando": comando,
        "codigo": codigo,
        "marca_temporal": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
