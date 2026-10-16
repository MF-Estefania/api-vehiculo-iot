from pydantic import BaseModel, ConfigDict, Field


class DemoOut(BaseModel):
    id_demo: int
    id_vehiculo: int
    nombre: str
    descripcion: str | None = None
    activo: bool


class MovimientoDemoOut(BaseModel):
    id_demo_movimiento: int
    orden: int
    id_comando: int
    comando: str
    codigo: int
    duracion_ms: int
    pausa_ms: int


class DemoIniciadaOut(BaseModel):
    id_vehiculo: int
    id_demo: int
    nombre: str
    total_movimientos: int
    mensaje: str


class DemoCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., min_length=1, max_length=80, examples=["Demo larga"])
    descripcion: str = Field("", max_length=255)


class DemoActualizar(DemoCrear):
    """sp_actualizar_demo exige todos los campos, incluido `activo`."""

    activo: bool


class MovimientoDemoCrear(BaseModel):
    id_comando: int = Field(..., gt=0, examples=[1])
    orden: int = Field(..., ge=1, examples=[1])
    duracion_ms: int = Field(..., ge=0, le=600000, examples=[3000])
    pausa_ms: int = Field(0, ge=0, le=600000, examples=[500])


class MovimientoDemoActualizar(MovimientoDemoCrear):
    """sp_actualizar_movimiento_demo reemplaza todos los campos del movimiento."""