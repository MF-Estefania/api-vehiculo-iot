from app.database import Database, db


class MisVehiculosService:
    def __init__(self, database: Database = db):
        self._db = database

    def listar_por_usuario(self, id_usuario: int, rol: str) -> list[dict]:
        with self._db.transaction() as cur:
            if rol in ("administradora", "administrador"):
                # Administrador puede ver todas las unidades
                cur.execute(
                    """
                    SELECT v.id_vehiculo, v.id_modelo, m.nombre_modelo, v.nombre, v.modelo,
                           v.numero_serie, v.descripcion, v.microcontrolador,
                           v.id_propietario, v.estado_comercial, v.activo,
                           COALESCE(e.conectado, 0) AS conectado
                    FROM vehiculos v
                    LEFT JOIN modelos_vehiculo m ON m.id_modelo = v.id_modelo
                    LEFT JOIN estado_vehiculo e ON e.id_vehiculo = v.id_vehiculo
                    WHERE v.activo = 1
                    ORDER BY v.id_vehiculo
                    """
                )
            else:
                # Usuario comprador solo ve sus vehículos asignados
                cur.execute(
                    """
                    SELECT v.id_vehiculo, v.id_modelo, m.nombre_modelo, v.nombre, v.modelo,
                           v.numero_serie, v.descripcion, v.microcontrolador,
                           v.id_propietario, v.estado_comercial, v.activo,
                           COALESCE(e.conectado, 0) AS conectado
                    FROM vehiculos v
                    LEFT JOIN modelos_vehiculo m ON m.id_modelo = v.id_modelo
                    LEFT JOIN estado_vehiculo e ON e.id_vehiculo = v.id_vehiculo
                    WHERE v.id_propietario = %s AND v.activo = 1
                    ORDER BY v.id_vehiculo
                    """,
                    (id_usuario,),
                )
            return cur.fetchall()

    def verificar_propiedad(self, id_usuario: int, rol: str, id_vehiculo: int) -> bool:
        if rol in ("administradora", "administrador"):
            return True
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT id_vehiculo
                FROM vehiculos
                WHERE id_vehiculo = %s AND id_propietario = %s AND activo = 1
                """,
                (id_vehiculo, id_usuario),
            )
            return cur.fetchone() is not None
