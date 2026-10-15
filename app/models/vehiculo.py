from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehiculoOut(BaseModel):
    """Vehículo tal como lo devuelve la API."""

    id_vehiculo: int
    nombre: str
    modelo: str | None = None
    descripcion: str | None = None
    microcontrolador: str | None = None
    fecha_registro: datetime | None = None
    activo: bool


class VehiculoCrear(BaseModel):
    """Datos para registrar un vehículo. Los largos coinciden con la tabla."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., min_length=1, max_length=80, examples=["Excavadora IoT"])
    modelo: str = Field(..., min_length=1, max_length=80, examples=["EX-01"])
    descripcion: str = Field("", max_length=255)
    microcontrolador: str = Field(..., min_length=1, max_length=50, examples=["ESP32"])


class VehiculoActualizar(VehiculoCrear):
    """sp_actualizar_vehiculo exige todos los campos, incluido `activo`."""

    activo: bool