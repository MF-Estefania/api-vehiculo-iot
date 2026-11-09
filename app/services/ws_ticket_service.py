import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.database import Database


class WsTicketService:
    DURACION_SEGUNDOS = 30

    def __init__(self):
        self.db = Database()

    @staticmethod
    def hash_ticket(ticket):
        return hashlib.sha256(ticket.encode("utf-8")).hexdigest()

    def crear_ticket(self, id_usuario, id_vehiculo):
        ticket = secrets.token_urlsafe(32)
        ticket_hash = self.hash_ticket(ticket)

        expiracion = datetime.now(timezone.utc) + timedelta(
            seconds=self.DURACION_SEGUNDOS
        )

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO tickets_ws
                    (id_usuario, id_vehiculo,
                     ticket_hash, fecha_expiracion)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    id_usuario,
                    id_vehiculo,
                    ticket_hash,
                    expiracion.replace(tzinfo=None),
                ),
            )

        return {
            "ticket": ticket,
            "expires_in": self.DURACION_SEGUNDOS,
        }

    def consumir_ticket(self, ticket, id_vehiculo):
        if not ticket:
            return False

        ticket_hash = self.hash_ticket(ticket)

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                UPDATE tickets_ws t
                INNER JOIN usuarios_app u
                    ON u.id_usuario = t.id_usuario
                SET t.utilizado = 1
                WHERE t.ticket_hash = %s
                  AND t.id_vehiculo = %s
                  AND t.utilizado = 0
                  AND t.fecha_expiracion > UTC_TIMESTAMP()
                  AND u.activo = 1
                """,
                (ticket_hash, id_vehiculo),
            )

            return cursor.rowcount == 1
