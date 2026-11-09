import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash

from app.database import Database


class AuthService:
    DURACION_SESION_HORAS = 8

    def __init__(self):
        self.db = Database()
        self.password_hash = PasswordHash.recommended()

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def iniciar_sesion(self, nombre_usuario, password):
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                SELECT id_usuario, nombre_usuario,
                       password_hash, rol, activo
                FROM usuarios_app
                WHERE nombre_usuario = %s
                """,
                (nombre_usuario,),
            )
            usuario = cursor.fetchone()

        if not usuario or not usuario["activo"]:
            return None

        if not self.password_hash.verify(
            password, usuario["password_hash"]
        ):
            return None

        token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(token)

        expiracion = datetime.now(timezone.utc) + timedelta(
            hours=self.DURACION_SESION_HORAS
        )

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO sesiones_app
                    (id_usuario, token_hash, fecha_expiracion)
                VALUES (%s, %s, %s)
                """,
                (
                    usuario["id_usuario"],
                    token_hash,
                    expiracion.replace(tzinfo=None),
                ),
            )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.DURACION_SESION_HORAS * 3600,
            "usuario": {
                "id_usuario": usuario["id_usuario"],
                "nombre_usuario": usuario["nombre_usuario"],
                "rol": usuario["rol"],
            },
        }

    def verificar_sesion(self, token):
        if not token:
            return None

        token_hash = self.hash_token(token)

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                SELECT u.id_usuario, u.nombre_usuario, u.rol
                FROM sesiones_app s
                INNER JOIN usuarios_app u
                    ON u.id_usuario = s.id_usuario
                WHERE s.token_hash = %s
                  AND s.revocada = 0
                  AND s.fecha_expiracion > UTC_TIMESTAMP()
                  AND u.activo = 1
                """,
                (token_hash,),
            )
            return cursor.fetchone()

    def cerrar_sesion(self, token):
        token_hash = self.hash_token(token)

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                UPDATE sesiones_app
                SET revocada = 1
                WHERE token_hash = %s
                """,
                (token_hash,),
            )
            return cursor.fetchone()
