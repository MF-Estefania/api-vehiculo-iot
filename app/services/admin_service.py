from app.database import Database, db
from app.exceptions import ConflictoError, RecursoNoEncontrado


class AdminService:
    def __init__(self, database: Database = db):
        self._db = database

    # 1. Dashboard de Métricas
    def obtener_metricas(self) -> dict:
        with self._db.transaction() as cur:
            # Modelos
            cur.execute("SELECT COUNT(*) AS total FROM modelos_vehiculo WHERE activo = 1")
            total_modelos = cur.fetchone()["total"]

            # Unidades físicas
            cur.execute("SELECT COUNT(*) AS total FROM vehiculos WHERE activo = 1")
            total_unidades = cur.fetchone()["total"]

            # Unidades por estado comercial
            cur.execute(
                """
                SELECT estado_comercial, COUNT(*) AS cantidad
                FROM vehiculos
                WHERE activo = 1
                GROUP BY estado_comercial
                """
            )
            estados = {r["estado_comercial"]: r["cantidad"] for r in cur.fetchall()}

            # Clientes compradores
            cur.execute("SELECT COUNT(*) AS total FROM usuarios_app WHERE rol = 'usuario' AND activo = 1")
            total_clientes = cur.fetchone()["total"]

            # Demos
            cur.execute("SELECT COUNT(*) AS total FROM demos WHERE activo = 1")
            total_demos = cur.fetchone()["total"]

            # Historial de operaciones totales
            cur.execute("SELECT COUNT(*) AS total FROM historial_comandos")
            total_movimientos = cur.fetchone()["total"]

            # Estado actual de conexion de las unidades
            cur.execute(
                """
                SELECT v.id_vehiculo, v.nombre, v.estado_comercial,
                       COALESCE(e.conectado, 0) AS conectado,
                       e.fecha_actualizacion
                FROM vehiculos v
                LEFT JOIN estado_vehiculo e ON e.id_vehiculo = v.id_vehiculo
                WHERE v.activo = 1
                """
            )
            estado_unidades = cur.fetchall()

        return {
            "modelos": total_modelos,
            "unidades_totales": total_unidades,
            "disponibles": estados.get("disponible", 0),
            "vendidas": estados.get("vendido", 0),
            "exhibicion": estados.get("exhibicion", 0),
            "mantenimiento": estados.get("mantenimiento", 0),
            "clientes": total_clientes,
            "demos": total_demos,
            "movimientos_historicos": total_movimientos,
            "estado_unidades": estado_unidades,
        }

    # 2. Catálogo de Modelos
    def listar_modelos(self) -> list[dict]:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT id_modelo, nombre_modelo, descripcion, microcontrolador, activo, fecha_creacion
                FROM modelos_vehiculo
                ORDER BY id_modelo
                """
            )
            return cur.fetchall()

    def crear_modelo(self, datos: dict) -> dict:
        with self._db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO modelos_vehiculo (nombre_modelo, descripcion, microcontrolador, activo)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    datos["nombre_modelo"],
                    datos.get("descripcion", ""),
                    datos.get("microcontrolador", "ESP8266"),
                    int(datos.get("activo", True)),
                ),
            )
            nuevo_id = cur.lastrowid
            cur.execute("SELECT * FROM modelos_vehiculo WHERE id_modelo = %s", (nuevo_id,))
            return cur.fetchone()

    def actualizar_modelo(self, id_modelo: int, datos: dict) -> dict:
        with self._db.transaction() as cur:
            cur.execute("SELECT id_modelo FROM modelos_vehiculo WHERE id_modelo = %s", (id_modelo,))
            if not cur.fetchone():
                raise RecursoNoEncontrado(f"No existe el modelo {id_modelo}")

            cur.execute(
                """
                UPDATE modelos_vehiculo
                SET nombre_modelo = %s, descripcion = %s, microcontrolador = %s, activo = %s
                WHERE id_modelo = %s
                """,
                (
                    datos["nombre_modelo"],
                    datos.get("descripcion", ""),
                    datos.get("microcontrolador", "ESP8266"),
                    int(datos.get("activo", True)),
                    id_modelo,
                ),
            )
            cur.execute("SELECT * FROM modelos_vehiculo WHERE id_modelo = %s", (id_modelo,))
            return cur.fetchone()

    # 3. Inventario de Unidades Físicas
    def listar_unidades(self) -> list[dict]:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT v.id_vehiculo, v.id_modelo, m.nombre_modelo, v.nombre, v.modelo,
                       v.numero_serie, v.descripcion, v.microcontrolador,
                       v.id_propietario, u.nombre_usuario AS propietario,
                       v.estado_comercial, v.activo, v.fecha_registro,
                       COALESCE(e.conectado, 0) AS conectado
                FROM vehiculos v
                LEFT JOIN modelos_vehiculo m ON m.id_modelo = v.id_modelo
                LEFT JOIN usuarios_app u ON u.id_usuario = v.id_propietario
                LEFT JOIN estado_vehiculo e ON e.id_vehiculo = v.id_vehiculo
                ORDER BY v.id_vehiculo
                """
            )
            return cur.fetchall()

    def crear_unidad(self, datos: dict) -> dict:
        with self._db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO vehiculos (id_modelo, nombre, modelo, numero_serie, descripcion, microcontrolador, id_propietario, estado_comercial, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    datos.get("id_modelo", 1),
                    datos["nombre"],
                    datos.get("modelo", "TR-01"),
                    datos.get("numero_serie"),
                    datos.get("descripcion", ""),
                    datos.get("microcontrolador", "ESP8266"),
                    datos.get("id_propietario"),
                    datos.get("estado_comercial", "disponible"),
                    int(datos.get("activo", True)),
                ),
            )
            nuevo_id = cur.lastrowid
            # Crear estado inicial
            cur.execute(
                "INSERT INTO estado_vehiculo (id_vehiculo, conectado) VALUES (%s, 0)",
                (nuevo_id,),
            )
            # Copiar comandos base del modelo o vehículo 1
            cur.execute(
                """
                INSERT INTO comandos (id_vehiculo, nombre, codigo, descripcion, activo)
                SELECT %s, nombre, codigo, descripcion, activo
                FROM comandos
                WHERE id_vehiculo = 1
                """,
                (nuevo_id,),
            )

        return self.obtener_unidad(nuevo_id)

    def obtener_unidad(self, id_vehiculo: int) -> dict:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT v.id_vehiculo, v.id_modelo, m.nombre_modelo, v.nombre, v.modelo,
                       v.numero_serie, v.descripcion, v.microcontrolador,
                       v.id_propietario, u.nombre_usuario AS propietario,
                       v.estado_comercial, v.activo, v.fecha_registro,
                       COALESCE(e.conectado, 0) AS conectado
                FROM vehiculos v
                LEFT JOIN modelos_vehiculo m ON m.id_modelo = v.id_modelo
                LEFT JOIN usuarios_app u ON u.id_usuario = v.id_propietario
                LEFT JOIN estado_vehiculo e ON e.id_vehiculo = v.id_vehiculo
                WHERE v.id_vehiculo = %s
                """,
                (id_vehiculo,),
            )
            unidad = cur.fetchone()
            if not unidad:
                raise RecursoNoEncontrado(f"No existe la unidad {id_vehiculo}")
            return unidad

    def actualizar_unidad(self, id_vehiculo: int, datos: dict) -> dict:
        self.obtener_unidad(id_vehiculo)
        with self._db.transaction() as cur:
            cur.execute(
                """
                UPDATE vehiculos
                SET id_modelo = %s, nombre = %s, modelo = %s, numero_serie = %s,
                    descripcion = %s, microcontrolador = %s, id_propietario = %s,
                    estado_comercial = %s, activo = %s
                WHERE id_vehiculo = %s
                """,
                (
                    datos.get("id_modelo"),
                    datos["nombre"],
                    datos.get("modelo"),
                    datos.get("numero_serie"),
                    datos.get("descripcion", ""),
                    datos.get("microcontrolador", "ESP8266"),
                    datos.get("id_propietario"),
                    datos.get("estado_comercial", "disponible"),
                    int(datos.get("activo", True)),
                    id_vehiculo,
                ),
            )
        return self.obtener_unidad(id_vehiculo)

    def asignar_unidad(self, id_vehiculo: int, id_usuario: int | None, estado_comercial: str | None = None) -> dict:
        self.obtener_unidad(id_vehiculo)
        if id_usuario is not None:
            with self._db.transaction() as cur:
                cur.execute("SELECT id_usuario FROM usuarios_app WHERE id_usuario = %s AND activo = 1", (id_usuario,))
                if not cur.fetchone():
                    raise RecursoNoEncontrado(f"El cliente con ID {id_usuario} no existe o no está activo")

        nuevo_estado = estado_comercial or ("vendido" if id_usuario else "disponible")

        with self._db.transaction() as cur:
            cur.execute(
                """
                UPDATE vehiculos
                SET id_propietario = %s, estado_comercial = %s
                WHERE id_vehiculo = %s
                """,
                (id_usuario, nuevo_estado, id_vehiculo),
            )

        return self.obtener_unidad(id_vehiculo)

    # 4. Lista de Clientes
    def listar_clientes(self) -> list[dict]:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT u.id_usuario, u.nombre_usuario, u.rol, u.activo, u.fecha_creacion,
                       COUNT(v.id_vehiculo) AS unidades_asignadas
                FROM usuarios_app u
                LEFT JOIN vehiculos v ON v.id_propietario = u.id_usuario AND v.activo = 1
                WHERE u.rol IN ('usuario', 'administradora', 'administrador')
                GROUP BY u.id_usuario
                ORDER BY u.id_usuario
                """
            )
            return cur.fetchall()
