from app.database import Database, db
from app.services.vehiculo_service import VehiculoService


class EstadoService:
    """Consulta del último estado registrado de un vehículo."""

    def __init__(
        self, database: Database = db, vehiculos: VehiculoService | None = None
    ) -> None:
        self._db = database
        self._vehiculos = vehiculos or VehiculoService(database)

    def obtener(self, id_vehiculo: int) -> dict | None:
        """Devuelve el estado, o None si el vehículo aún no tiene ninguno."""
        self._vehiculos.obtener(id_vehiculo)  # 404 si el vehículo no existe
        filas = self._db.call_procedure("sp_obtener_estado", (id_vehiculo,))
        return filas[0] if filas else None