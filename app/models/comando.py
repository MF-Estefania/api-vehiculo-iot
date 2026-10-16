from pydantic import BaseModel, ConfigDict, Field


class ComandoOut(BaseModel):
    """Comando del catálogo de un vehículo."""

    id_comando: int
    id_vehiculo: int
    nombre: str
    codigo: int
    descripcion: str | None = None
    activo: bool


class ComandoCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., min_length=1, max_length=60, examples=["adelante"])
    codigo: int = Field(..., ge=0, examples=[1])
    descripcion: str = Field("", max_length=255)


class ComandoActualizar(ComandoCrear):
    """sp_actualizar_comando exige todos los campos, incluido `activo`."""

    activo: bool