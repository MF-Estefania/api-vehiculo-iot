from datetime import datetime

from pydantic import BaseModel


class EstadoOut(BaseModel):
    """Último estado registrado del vehículo."""

    id_vehiculo: int
    vehiculo: str
    id_comando: int | None = None
    comando: str | None = None
    codigo: int | None = None
    conectado: bool
    fecha_actualizacion: datetime | None = None