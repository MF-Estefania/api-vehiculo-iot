from app.database import Database, DatabaseError, db
from app.exceptions import ConflictoError, RecursoNoEncontrado
from app.models.demo import DemoActualizar, DemoCrear, MovimientoDemoCrear
from app.services.comando_service import ComandoService
from app.services.vehiculo_service import VehiculoService

_DUPLICADO = 1062  # MySQL: valor repetido en una columna única
_FILAS_RELACIONADAS = 1451  # MySQL: otras filas dependen de ésta


class DemoService:
    """Reglas de negocio de las DEMO y de sus movimientos."""

    def __init__(
        self, database: Database = db, vehiculos: VehiculoService | None = None
    ) -> None:
        self._db = database
        self._vehiculos = vehiculos or VehiculoService(database)
        self._comandos = ComandoService(database, self._vehiculos)

    # --- DEMO -------------------------------------------------------------

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

    def crear(self, id_vehiculo: int, datos: DemoCrear) -> dict:
        self._vehiculos.obtener(id_vehiculo)
        filas = self._db.call_procedure(
            "sp_crear_demo", (id_vehiculo, datos.nombre, datos.descripcion)
        )
        return self.obtener(id_vehiculo, filas[0]["id_demo"])

    def actualizar(self, id_vehiculo: int, id_demo: int, datos: DemoActualizar) -> dict:
        self.obtener(id_vehiculo, id_demo)  # 404 si no existe o es de otro vehículo
        self._db.call_procedure(
            "sp_actualizar_demo",
            (id_demo, datos.nombre, datos.descripcion, int(datos.activo)),
        )
        return self.obtener(id_vehiculo, id_demo)

    def eliminar(self, id_vehiculo: int, id_demo: int) -> None:
        self.obtener(id_vehiculo, id_demo)
        try:
            self._db.call_procedure("sp_eliminar_demo", (id_demo,))
        except DatabaseError as error:
            if error.codigo == _FILAS_RELACIONADAS:
                raise ConflictoError(
                    "No se puede eliminar: la DEMO todavía tiene movimientos"
                ) from None
            raise

    # --- Movimientos de la DEMO ------------------------------------------

    def listar_movimientos(self, id_vehiculo: int, id_demo: int) -> list[dict]:
        self.obtener(id_vehiculo, id_demo)  # verifica existencia y pertenencia
        return self.movimientos(id_demo)

    def movimientos(self, id_demo: int) -> list[dict]:
        """Movimientos ordenados. No verifica pertenencia: úsalo tras obtener()."""
        return self._db.call_procedure("sp_obtener_movimientos_demo", (id_demo,))

    def _buscar_movimiento(self, id_demo: int, id_movimiento: int) -> dict:
        for movimiento in self.movimientos(id_demo):
            if movimiento["id_demo_movimiento"] == id_movimiento:
                return movimiento
        raise RecursoNoEncontrado(
            f"El movimiento {id_movimiento} no existe en la DEMO {id_demo}"
        )

    def agregar_movimiento(
        self, id_vehiculo: int, id_demo: int, datos: MovimientoDemoCrear
    ) -> list[dict]:
        self.obtener(id_vehiculo, id_demo)
        # El comando debe pertenecer al mismo vehículo que la DEMO (404 si no).
        self._comandos.obtener(id_vehiculo, datos.id_comando)
        try:
            self._db.call_procedure(
                "sp_agregar_movimiento_demo",
                (id_demo, datos.id_comando, datos.orden, datos.duracion_ms, datos.pausa_ms),
            )
        except DatabaseError as error:
            self._traducir(error)
            raise
        return self.movimientos(id_demo)

    def actualizar_movimiento(
        self,
        id_vehiculo: int,
        id_demo: int,
        id_movimiento: int,
        datos: MovimientoDemoCrear,
    ) -> dict:
        self.obtener(id_vehiculo, id_demo)
        self._buscar_movimiento(id_demo, id_movimiento)  # 404 si no existe
        self._comandos.obtener(id_vehiculo, datos.id_comando)
        try:
            self._db.call_procedure(
                "sp_actualizar_movimiento_demo",
                (id_movimiento, datos.id_comando, datos.orden, datos.duracion_ms, datos.pausa_ms),
            )
        except DatabaseError as error:
            self._traducir(error)
            raise
        return self._buscar_movimiento(id_demo, id_movimiento)

    def eliminar_movimiento(self, id_vehiculo: int, id_demo: int, id_movimiento: int) -> None:
        self.obtener(id_vehiculo, id_demo)
        self._buscar_movimiento(id_demo, id_movimiento)
        self._db.call_procedure("sp_eliminar_movimiento_demo", (id_movimiento,))

    @staticmethod
    def _traducir(error: DatabaseError) -> None:
        if error.codigo == _DUPLICADO:
            raise ConflictoError("Ya existe un movimiento con ese orden en la DEMO") from None