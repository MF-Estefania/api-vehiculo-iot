from pydantic import BaseModel, ConfigDict, Field

from app.models.estado import EstadoOut


class MovimientoCrear(BaseModel):
    """Solicitud para ejecutar un comando que ya existe en el catálogo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id_comando: int = Field(..., gt=0, examples=[1])
    origen: str = Field("api", min_length=1, max_length=30, examples=["swagger"])


class MovimientoOut(BaseModel):
    """Resultado de registrar un movimiento individual."""

    id_vehiculo: int
    comando: str
    codigo: int
    origen: str
    estado: EstadoOut
    clientes_notificados: int