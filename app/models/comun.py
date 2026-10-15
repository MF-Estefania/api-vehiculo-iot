from pydantic import BaseModel


class MensajeOut(BaseModel):
    """Respuesta simple para operaciones sin datos que devolver."""

    mensaje: str