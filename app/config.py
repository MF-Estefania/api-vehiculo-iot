import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Se lanza cuando falta o es inválida una variable de entorno."""


class Settings:
    """Lee y expone la configuración de la aplicación desde variables de entorno.

    Responsabilidad única: configuración. No abre conexiones a la base de datos.
    """

    _REQUERIDAS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")

    def __init__(self) -> None:
        faltantes = [nombre for nombre in self._REQUERIDAS if not os.getenv(nombre)]
        if faltantes:
            raise ConfigError(
                "Faltan variables de entorno: " + ", ".join(faltantes)
            )

        try:
            self._db_port = int(os.getenv("DB_PORT"))
        except ValueError:
            raise ConfigError("DB_PORT debe ser un número entero") from None

        self._db_host = os.getenv("DB_HOST")
        self._db_name = os.getenv("DB_NAME")
        self._db_user = os.getenv("DB_USER")
        self._db_password = os.getenv("DB_PASSWORD")

    @property
    def db_host(self) -> str:
        return self._db_host

    @property
    def db_port(self) -> int:
        return self._db_port

    @property
    def db_name(self) -> str:
        return self._db_name

    @property
    def db_user(self) -> str:
        return self._db_user

    @property
    def db_password(self) -> str:
        return self._db_password

    def __repr__(self) -> str:
        # Nunca muestra la contraseña, por si el objeto se imprime en un log.
        return (
            f"Settings(db_host={self._db_host!r}, db_port={self._db_port}, "
            f"db_name={self._db_name!r}, db_user={self._db_user!r}, "
            "db_password='***')"
        )


# Instancia única que el resto de la aplicación importará.
settings = Settings()