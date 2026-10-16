from app.database import Database, db
from app.services.vehiculo_service import VehiculoService


class HistorialService:
    """Consulta de la bitácora de movimientos individuales."""

    LIMITE = 10  # la práctica exige como máximo los diez más recientes

    def __init__(
        self, database: Database = db, vehiculos: VehiculoService | None = None
    ) -> None:
        self._db = database
        self._vehiculos = vehiculos or VehiculoService(database)

    def ultimos(self, id_vehiculo: int) -> list[dict]:
        self._vehiculos.obtener(id_vehiculo)  # 404 si el vehículo no existe
        filas = self._db.call_procedure("sp_obtener_historial", (id_vehiculo,))
        # El SP ya ordena del más reciente al más antiguo y devuelve todo:
        # el límite lo aplica el servicio. En RDS el historial se conserva completo.
        return filas[: self.LIMITE]