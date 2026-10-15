class RecursoNoEncontrado(Exception):
    """El recurso solicitado no existe (se traduce a HTTP 404)."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ConflictoError(Exception):
    """La operación choca con el estado actual de los datos (HTTP 409)."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje