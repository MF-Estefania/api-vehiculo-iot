from datetime import datetime

from pydantic import BaseModel


class VehiculoOut(BaseModel):
    """Vehículo tal como lo devuelve la API."""

    id_vehiculo: int
    nombre: str
    modelo: str | None = None
    descripcion: str | None = None
    microcontrolador: str | None = None
    fecha_registro: datetime | None = None
    activo: bool