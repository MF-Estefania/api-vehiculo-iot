from datetime import datetime

from pydantic import BaseModel


class HistorialOut(BaseModel):
    """Un movimiento individual registrado en la bitácora."""

    id_historial: int
    id_vehiculo: int
    comando: str | None = None
    codigo: int | None = None
    fecha_hora: datetime | None = None
    origen: str