from app.database import Database, db
from app.exceptions import RecursoNoEncontrado

from app.database import Database, DatabaseError, db
from app.exceptions import ConflictoError, RecursoNoEncontrado
from app.models.vehiculo import VehiculoActualizar, VehiculoCrear

# Código de MySQL: no se puede borrar una fila porque otras dependen de ella.
_ERROR_FILAS_RELACIONADAS = 1451


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

    def crear(self, datos: VehiculoCrear) -> dict:
        filas = self._db.call_procedure(
            "sp_crear_vehiculo",
            (datos.nombre, datos.modelo, datos.descripcion, datos.microcontrolador),
        )
        return self.obtener(filas[0]["id_vehiculo"])

    def actualizar(self, id_vehiculo: int, datos: VehiculoActualizar) -> dict:
        self.obtener(id_vehiculo)  # 404 si no existe: el SP no avisaría
        self._db.call_procedure(
            "sp_actualizar_vehiculo",
            (
                id_vehiculo,
                datos.nombre,
                datos.modelo,
                datos.descripcion,
                datos.microcontrolador,
                int(datos.activo),
            ),
        )
        return self.obtener(id_vehiculo)

    def eliminar(self, id_vehiculo: int) -> None:
        self.obtener(id_vehiculo)  # 404 si no existe
        try:
            self._db.call_procedure("sp_eliminar_vehiculo", (id_vehiculo,))
        except DatabaseError as error:
            if error.codigo == _ERROR_FILAS_RELACIONADAS:
                raise ConflictoError(
                    "No se puede eliminar: el vehículo tiene datos relacionados"
                ) from None
            raise