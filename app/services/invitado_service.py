import secrets
from datetime import datetime, timedelta, timezone

from app.database import Database, db
from app.exceptions import ConflictoError, RecursoNoEncontrado


class InvitadoService:
    DURACION_DEMO_SEGUNDOS = 180  # 3 minutos de demostración

    def __init__(self, database: Database = db):
        self._db = database

    def obtener_catalogo(self) -> list[dict]:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT m.id_modelo, m.nombre_modelo, m.descripcion, m.microcontrolador,
                       COUNT(v.id_vehiculo) AS unidades_exhibicion,
                       (
                           SELECT COUNT(*)
                           FROM reservas_exhibicion r
                           JOIN vehiculos ve ON ve.id_vehiculo = r.id_vehiculo
                           WHERE ve.id_modelo = m.id_modelo
                             AND r.activa = 1
                             AND r.fecha_fin > UTC_TIMESTAMP()
                       ) AS reservas_activas
                FROM modelos_vehiculo m
                LEFT JOIN vehiculos v ON v.id_modelo = m.id_modelo AND v.estado_comercial = 'exhibicion' AND v.activo = 1
                WHERE m.activo = 1
                GROUP BY m.id_modelo
                """
            )
            return cur.fetchall()

    def solicitar_reserva(self, id_vehiculo: int, id_usuario: int = 3, ip_origen: str = None) -> dict:
        with self._db.transaction() as cur:
            # 1. Verificar que el vehículo sea de exhibición y esté activo
            cur.execute(
                """
                SELECT id_vehiculo, nombre, estado_comercial, activo
                FROM vehiculos
                WHERE id_vehiculo = %s
                """,
                (id_vehiculo,),
            )
            vehiculo = cur.fetchone()
            if not vehiculo or not vehiculo["activo"]:
                raise RecursoNoEncontrado("La unidad física no existe o no está activa")

            if vehiculo["estado_comercial"] != "exhibicion":
                raise ConflictoError(
                    "Esta unidad no está autorizada para demostraciones públicas. Solo unidades en exhibición."
                )

            # 2. Exclusividad: Verificar si ya existe una reserva activa para este vehículo
            cur.execute(
                """
                SELECT id_reserva, fecha_fin,
                       TIMESTAMPDIFF(SECOND, UTC_TIMESTAMP(), fecha_fin) AS segundos_restantes
                FROM reservas_exhibicion
                WHERE id_vehiculo = %s
                  AND activa = 1
                  AND fecha_fin > UTC_TIMESTAMP()
                ORDER BY fecha_fin DESC
                LIMIT 1
                """,
                (id_vehiculo,),
            )
            reserva_activa = cur.fetchone()
            if reserva_activa and reserva_activa["segundos_restantes"] > 0:
                raise ConflictoError(
                    f"El vehículo está actualmente en demostración por otro usuario. Tiempo restante estimado: {reserva_activa['segundos_restantes']} segundos."
                )

            # 3. Crear nueva reserva exclusiva
            token = secrets.token_urlsafe(32)
            ahora = datetime.now(timezone.utc)
            fin = ahora + timedelta(seconds=self.DURACION_DEMO_SEGUNDOS)

            cur.execute(
                """
                INSERT INTO reservas_exhibicion
                    (id_vehiculo, id_usuario, token_sesion, fecha_inicio, fecha_fin, activa)
                VALUES (%s, %s, %s, %s, %s, 1)
                """,
                (
                    id_vehiculo,
                    id_usuario,
                    token,
                    ahora.strftime("%Y-%m-%d %H:%M:%S"),
                    fin.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            id_reserva = cur.lastrowid

            # 4. Devolver comandos permitidos para invitados (movimientos básicos y STOP)
            cur.execute(
                """
                SELECT id_comando, nombre, codigo, descripcion
                FROM comandos
                WHERE id_vehiculo = %s AND activo = 1
                ORDER BY id_comando
                """,
                (id_vehiculo,),
            )
            comandos_permitidos = cur.fetchall()

        return {
            "id_reserva": id_reserva,
            "id_vehiculo": id_vehiculo,
            "token_sesion": token,
            "duracion_segundos": self.DURACION_DEMO_SEGUNDOS,
            "expira_en": fin.isoformat(),
            "comandos_habilitados": comandos_permitidos,
        }

    def verificar_reserva_activa(self, id_vehiculo: int, token_sesion: str | None) -> bool:
        if not token_sesion:
            return False
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT id_reserva
                FROM reservas_exhibicion
                WHERE id_vehiculo = %s
                  AND token_sesion = %s
                  AND activa = 1
                  AND fecha_fin > UTC_TIMESTAMP()
                """,
                (id_vehiculo, token_sesion),
            )
            return cur.fetchone() is not None

    def finalizar_reserva(self, id_vehiculo: int, token_sesion: str | None) -> bool:
        with self._db.transaction() as cur:
            cur.execute(
                """
                UPDATE reservas_exhibicion
                SET activa = 0
                WHERE id_vehiculo = %s AND (token_sesion = %s OR %s IS NULL) AND activa = 1
                """,
                (id_vehiculo, token_sesion, token_sesion),
            )
            return cur.rowcount > 0
