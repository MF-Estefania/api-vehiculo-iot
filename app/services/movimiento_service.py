from app.database import Database, db
from app.exceptions import ConflictoError
from app.models.movimiento import MovimientoCrear
from app.services.comando_service import ComandoService
from app.services.vehiculo_service import VehiculoService


class MovimientoService:
    """Registra movimientos individuales: valida, actualiza estado e historial."""

    def __init__(self, database: Database = db) -> None:
        self._db = database
        self._vehiculos = VehiculoService(database)
        self._comandos = ComandoService(database, self._vehiculos)

    def registrar(self, id_vehiculo: int, datos: MovimientoCrear) -> dict:
        vehiculo = self._vehiculos.obtener(id_vehiculo)  # 404 si no existe
        if not vehiculo["activo"]:
            raise ConflictoError("El vehículo está inactivo")

        # 404 si el comando no existe o pertenece a otro vehículo
        comando = self._comandos.obtener(id_vehiculo, datos.id_comando)
        if not comando["activo"]:
            raise ConflictoError("El comando está inactivo")

        with self._db.transaction() as cursor:
            actual = Database.execute_procedure(cursor, "sp_obtener_estado", (id_vehiculo,))
            # Recibir un HTTP no prueba que el vehículo esté conectado:
            # se conserva el valor que ya tenía (0 si aún no hay estado).
            conectado = int(actual[0]["conectado"]) if actual else 0
            Database.execute_procedure(
                cursor, "sp_actualizar_estado", (id_vehiculo, datos.id_comando, conectado)
            )
            Database.execute_procedure(
                cursor,
                "sp_registrar_historial",
                (id_vehiculo, datos.id_comando, datos.origen),
            )
        # Al salir del bloque, la transacción ya está confirmada en RDS.

        estado = self._db.call_procedure("sp_obtener_estado", (id_vehiculo,))[0]
        return {
            "id_vehiculo": id_vehiculo,
            "comando": comando["nombre"],
            "codigo": comando["codigo"],
            "origen": datos.origen,
            "estado": estado,
        }