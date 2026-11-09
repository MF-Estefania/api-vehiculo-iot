from datetime import datetime, timedelta, timezone

from app.database import Database


class LoginAttemptService:
    MAX_INTENTOS = 5
    VENTANA_MINUTOS = 15

    def __init__(self):
        self.db = Database()

    def esta_bloqueado(self, nombre_usuario: str) -> bool:
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM intentos_login
                WHERE nombre_usuario = %s
                  AND fecha_intento >= UTC_TIMESTAMP() - INTERVAL 15 MINUTE
                """,
                (nombre_usuario,),
            )
            resultado = cursor.fetchone()

        return resultado["total"] >= self.MAX_INTENTOS

    def registrar_fallo(self, nombre_usuario: str) -> None:
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO intentos_login (nombre_usuario)
                VALUES (%s)
                """,
                (nombre_usuario,),
            )

    def limpiar_intentos(self, nombre_usuario: str) -> None:
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                DELETE FROM intentos_login
                WHERE nombre_usuario = %s
                """,
                (nombre_usuario,),
            )
