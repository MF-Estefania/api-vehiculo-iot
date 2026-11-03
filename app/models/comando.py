
from pydantic import BaseModel, ConfigDict, Field


class ComandoOut(BaseModel):
    """Comando del catálogo de un vehículo."""

    id_comando: int
    id_vehiculo: int
    nombre: str
    codigo: str
    descripcion: str | None = None
    activo: bool


class ComandoCrear(BaseModel):
    """Datos para registrar un comando de cualquier vehículo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=60,
        examples=["Avanzar"]
    )

    codigo: str = Field(
        ...,
        min_length=1,
        max_length=20,
        examples=["B", "AV01"]
    )

    descripcion: str = Field(
        "",
        max_length=255
    )


class ComandoActualizar(ComandoCrear):
    """sp_actualizar_comando exige todos los campos, incluido activo."""

    activo: bool
