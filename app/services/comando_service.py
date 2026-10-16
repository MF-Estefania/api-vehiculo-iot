from app.database import Database, DatabaseError, db
from app.exceptions import ConflictoError, RecursoNoEncontrado
from app.models.comando import ComandoActualizar, ComandoCrear
from app.services.vehiculo_service import VehiculoService

_DUPLICADO = 1062  # MySQL: valor repetido en una columna única
_FILAS_RELACIONADAS = 1451  # MySQL: otras filas dependen de ésta


class ComandoService:
    """Reglas de negocio del catálogo de comandos de cada vehículo."""

    def __init__(
        self, database: Database = db, vehiculos: VehiculoService | None = None
    ) -> None:
        self._db = database
        self._vehiculos = vehiculos or VehiculoService(database)

    def listar(self, id_vehiculo: int) -> list[dict]:
        self._vehiculos.obtener(id_vehiculo)  # 404 si el vehículo no existe
        return self._db.call_procedure("sp_obtener_comandos_vehiculo", (id_vehiculo,))

    def obtener(self, id_vehiculo: int, id_comando: int) -> dict:
        """Devuelve el comando solo si pertenece a ese vehículo."""
        for comando in self.listar(id_vehiculo):
            if comando["id_comando"] == id_comando:
                return comando
        raise RecursoNoEncontrado(
            f"El comando {id_comando} no existe para el vehículo {id_vehiculo}"
        )

    def crear(self, id_vehiculo: int, datos: ComandoCrear) -> dict:
        self._vehiculos.obtener(id_vehiculo)
        try:
            filas = self._db.call_procedure(
                "sp_crear_comando",
                (id_vehiculo, datos.nombre, datos.codigo, datos.descripcion),
            )
        except DatabaseError as error:
            self._traducir(error)
            raise
        return self.obtener(id_vehiculo, filas[0]["id_comando"])

    def actualizar(
        self, id_vehiculo: int, id_comando: int, datos: ComandoActualizar
    ) -> dict:
        self.obtener(id_vehiculo, id_comando)  # 404 si no existe o es de otro vehículo
        try:
            self._db.call_procedure(
                "sp_actualizar_comando",
                (id_comando, datos.nombre, datos.codigo, datos.descripcion, int(datos.activo)),
            )
        except DatabaseError as error:
            self._traducir(error)
            raise
        return self.obtener(id_vehiculo, id_comando)

    def eliminar(self, id_vehiculo: int, id_comando: int) -> None:
        self.obtener(id_vehiculo, id_comando)
        try:
            self._db.call_procedure("sp_eliminar_comando", (id_comando,))
        except DatabaseError as error:
            self._traducir(error)
            raise

    @staticmethod
    def _traducir(error: DatabaseError) -> None:
        """Convierte códigos de MySQL en errores de negocio (HTTP 409)."""
        if error.codigo == _DUPLICADO:
            raise ConflictoError(
                "Ya existe un comando con ese nombre o código para el vehículo"
            ) from None
        if error.codigo == _FILAS_RELACIONADAS:
            raise ConflictoError(
                "No se puede eliminar: el comando se usa en una DEMO o en el historial"
            ) from None