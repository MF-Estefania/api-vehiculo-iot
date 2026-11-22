from app.database import Database, db


class AuditoriaService:
    def __init__(self, database: Database = db):
        self._db = database

    def registrar(
        self,
        accion: str,
        recurso: str,
        detalle: str | None = None,
        id_usuario: int | None = None,
        nombre_usuario: str | None = None,
        rol: str | None = None,
        ip_origen: str | None = None,
        resultado: str = "EXITO",
    ) -> None:
        try:
            with self._db.transaction() as cur:
                cur.execute(
                    """
                    INSERT INTO bitacora_auditoria
                        (id_usuario, nombre_usuario, rol, accion, recurso, detalle, ip_origen, resultado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_usuario,
                        nombre_usuario,
                        rol,
                        accion,
                        recurso,
                        detalle,
                        ip_origen,
                        resultado,
                    ),
                )
        except Exception as e:
            # Nunca dejamos caer una petición por fallo en auditoría
            print(f"Error registrando auditoría: {e}")

    def listar(self, limite: int = 50) -> list[dict]:
        with self._db.transaction() as cur:
            cur.execute(
                """
                SELECT id_auditoria, fecha_hora, id_usuario, nombre_usuario, rol,
                       accion, recurso, detalle, ip_origen, resultado
                FROM bitacora_auditoria
                ORDER BY id_auditoria DESC
                LIMIT %s
                """,
                (limite,),
            )
            return cur.fetchall()
