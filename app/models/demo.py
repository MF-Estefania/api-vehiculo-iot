from pydantic import BaseModel


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