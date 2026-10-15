from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from app.config import settings


class DatabaseError(Exception):
    """Error de acceso a la base de datos, sin datos sensibles en el mensaje."""


class Database:
    """Único punto de acceso a MySQL (Amazon RDS).

    Responsabilidad única: abrir conexiones, ejecutar Stored Procedures y
    manejar transacciones. No contiene reglas de negocio.
    """

    _TIMEOUT_CONEXION = 10  # segundos

    def __init__(self) -> None:
        self._config = {
            "host": settings.db_host,
            "port": settings.db_port,
            "user": settings.db_user,
            "password": settings.db_password,
            "database": settings.db_name,
            "cursorclass": DictCursor,
            "charset": "utf8mb4",
            "connect_timeout": self._TIMEOUT_CONEXION,
            "autocommit": False,
        }

    def _connect(self):
        """Crea y devuelve una conexión nueva."""
        try:
            return pymysql.connect(**self._config)
        except pymysql.MySQLError:
            raise DatabaseError("No fue posible conectar con la base de datos") from None

    @staticmethod
    def execute_procedure(cursor, nombre: str, args: tuple = ()) -> list[dict]:
        """Ejecuta un SP con un cursor ya abierto y devuelve sus filas.

        Se usa dentro de transaction() cuando se necesita encadenar varios SP.
        El nombre del SP lo define el código, nunca el usuario; los valores
        viajan siempre como parámetros.
        """
        cursor.callproc(nombre, args)
        filas = list(cursor.fetchall())
        # Consume conjuntos de resultados restantes para poder reutilizar el cursor.
        while cursor.nextset():
            pass
        return filas

    def call_procedure(self, nombre: str, args: tuple = ()) -> list[dict]:
        """Ejecuta un SP y devuelve sus filas, confirmando el cambio si lo hubo."""
        conn = self._connect()
        try:
            with conn.cursor() as cursor:
                filas = self.execute_procedure(cursor, nombre, args)
            conn.commit()
            return filas
        except pymysql.MySQLError:
            conn.rollback()
            raise DatabaseError("No fue posible completar la operación") from None
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Entrega un cursor dentro de una transacción atómica.

        Hace commit si el bloque termina bien y rollback si hay una excepción.
        """
        conn = self._connect()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except pymysql.MySQLError:
            conn.rollback()
            raise DatabaseError("No fue posible completar la transacción") from None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def ping(self) -> bool:
        """Comprueba que RDS responde."""
        conn = self._connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() is not None
        except pymysql.MySQLError:
            raise DatabaseError("La base de datos no respondió") from None
        finally:
            conn.close()


# Instancia compartida que usarán los servicios.
db = Database()