from datetime import datetime, timezone


def crear_evento(
    tipo: str,
    id_vehiculo: int,
    comando: str | None = None,
    codigo: int | None = None,
    **extra,
) -> dict:
    """Construye un mensaje JSON estándar para los clientes WebSocket."""
    return {
        "tipo": tipo,
        "id_vehiculo": id_vehiculo,
        "comando": comando,
        "codigo": codigo,
        "marca_temporal": datetime.now(timezone.utc).isoformat(),
        **extra,
    }