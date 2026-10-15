from app.database import Database, db
from app.exceptions import RecursoNoEncontrado


class VehiculoService:
    """Reglas de negocio de vehículos. Solo habla con la BD a través de Database."""

    def __init__(self, database: Database = db) -> None:
        self._db = database

    def listar(self) -> list[dict]:
        return self._db.call_procedure("sp_obtener_vehiculos")

    def obtener(self, id_vehiculo: int) -> dict:
        filas = self._db.call_procedure("sp_obtener_vehiculo", (id_vehiculo,))
        if not filas:
            raise RecursoNoEncontrado(f"No existe el vehículo {id_vehiculo}")
        return filas[0]