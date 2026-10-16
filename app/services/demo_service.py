from app.database import Database, db
from app.exceptions import RecursoNoEncontrado
from app.services.vehiculo_service import VehiculoService


class DemoService:
    """Consulta de DEMO y de sus movimientos."""

    def __init__(
        self, database: Database = db, vehiculos: VehiculoService | None = None
    ) -> None:
        self._db = database
        self._vehiculos = vehiculos or VehiculoService(database)

    def listar(self, id_vehiculo: int) -> list[dict]:
        self._vehiculos.obtener(id_vehiculo)  # 404 si el vehículo no existe
        return self._db.call_procedure("sp_obtener_demos", (id_vehiculo,))

    def obtener(self, id_vehiculo: int, id_demo: int) -> dict:
        """Devuelve la DEMO solo si pertenece a ese vehículo."""
        for demo in self.listar(id_vehiculo):
            if demo["id_demo"] == id_demo:
                return demo
        raise RecursoNoEncontrado(
            f"La DEMO {id_demo} no existe para el vehículo {id_vehiculo}"
        )

    def listar_movimientos(self, id_vehiculo: int, id_demo: int) -> list[dict]:
        self.obtener(id_vehiculo, id_demo)  # verifica existencia y pertenencia
        return self.movimientos(id_demo)

    def movimientos(self, id_demo: int) -> list[dict]:
        """Movimientos ordenados. No verifica pertenencia: úsalo tras obtener()."""
        return self._db.call_procedure("sp_obtener_movimientos_demo", (id_demo,))