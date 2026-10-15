class RecursoNoEncontrado(Exception):
    """El recurso solicitado no existe (se traduce a HTTP 404)."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje