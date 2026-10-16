import asyncio
import logging
from dataclasses import dataclass, field

from app.database import Database, db
from app.exceptions import ConflictoError
from app.services.demo_service import DemoService
from app.services.vehiculo_service import VehiculoService
from app.websocket.eventos import crear_evento
from app.websocket.manager import ConnectionManager, manager

log = logging.getLogger(__name__)


@dataclass
class _Ejecucion:
    """Estado de una DEMO en curso."""

    id_demo: int
    nombre: str = ""
    cancelar: asyncio.Event = field(default_factory=asyncio.Event)
    tarea: asyncio.Task | None = None


class DemoRunner:
    """Ejecuta DEMO en segundo plano y transmite sus movimientos por WebSocket."""

    def __init__(
        self, database: Database = db, gestor: ConnectionManager = manager
    ) -> None:
        self._db = database
        self._gestor = gestor
        self._vehiculos = VehiculoService(database)
        self._demos = DemoService(database, self._vehiculos)
        self._activas: dict[int, _Ejecucion] = {}

    def activa(self, id_vehiculo: int) -> bool:
        return id_vehiculo in self._activas

    async def iniciar(self, id_vehiculo: int, id_demo: int) -> dict:
        # Reserva el vehículo antes de cualquier await: evita dos DEMO simultáneas.
        if id_vehiculo in self._activas:
            raise ConflictoError("Ya hay una DEMO en ejecución para este vehículo")
        ejecucion = _Ejecucion(id_demo=id_demo)
        self._activas[id_vehiculo] = ejecucion
        try:
            demo, movimientos = await asyncio.to_thread(
                self._preparar, id_vehiculo, id_demo
            )
        except BaseException:
            self._activas.pop(id_vehiculo, None)
            raise

        ejecucion.nombre = demo["nombre"]
        ejecucion.tarea = asyncio.create_task(
            self._ejecutar(id_vehiculo, ejecucion, movimientos)
        )
        return {
            "id_vehiculo": id_vehiculo,
            "id_demo": id_demo,
            "nombre": demo["nombre"],
            "total_movimientos": len(movimientos),
            "mensaje": "DEMO iniciada; los movimientos se transmiten por WebSocket",
        }

    def cancelar(self, id_vehiculo: int) -> None:
        ejecucion = self._activas.get(id_vehiculo)
        if ejecucion is None:
            raise ConflictoError("No hay una DEMO en ejecución para este vehículo")
        ejecucion.cancelar.set()

    # --- Internos ---------------------------------------------------------

    def _preparar(self, id_vehiculo: int, id_demo: int):
        """Valida y carga los movimientos (código bloqueante: corre en un hilo)."""
        vehiculo = self._vehiculos.obtener(id_vehiculo)  # 404 si no existe
        if not vehiculo["activo"]:
            raise ConflictoError("El vehículo está inactivo")
        demo = self._demos.obtener(id_vehiculo, id_demo)  # 404 si no es de ese vehículo
        if not demo["activo"]:
            raise ConflictoError("La DEMO está inactiva")
        movimientos = self._demos.movimientos(id_demo)
        if not movimientos:
            raise ConflictoError("La DEMO no tiene movimientos")
        return demo, movimientos

    def _actualizar_estado(self, id_vehiculo: int, id_comando: int) -> None:
        """Actualiza el último estado. NO registra historial: es una DEMO."""
        with self._db.transaction() as cursor:
            actual = Database.execute_procedure(cursor, "sp_obtener_estado", (id_vehiculo,))
            conectado = int(actual[0]["conectado"]) if actual else 0
            Database.execute_procedure(
                cursor, "sp_actualizar_estado", (id_vehiculo, id_comando, conectado)
            )

    @staticmethod
    async def _esperar(milisegundos: int, cancelar: asyncio.Event) -> bool:
        """Espera sin bloquear. Devuelve True si se canceló durante la espera."""
        if milisegundos <= 0:
            return cancelar.is_set()
        try:
            await asyncio.wait_for(cancelar.wait(), timeout=milisegundos / 1000)
            return True
        except asyncio.TimeoutError:
            return False

    async def _ejecutar(
        self, id_vehiculo: int, ejecucion: _Ejecucion, movimientos: list[dict]
    ) -> None:
        total = len(movimientos)
        base = {"id_demo": ejecucion.id_demo, "nombre_demo": ejecucion.nombre}
        try:
            await self._gestor.difundir(
                id_vehiculo,
                crear_evento("demo_inicio", id_vehiculo, total_movimientos=total, **base),
            )
            for indice, mov in enumerate(movimientos, start=1):
                if ejecucion.cancelar.is_set():
                    break
                await asyncio.to_thread(
                    self._actualizar_estado, id_vehiculo, mov["id_comando"]
                )
                if ejecucion.cancelar.is_set():
                    break
                await self._gestor.difundir(
                    id_vehiculo,
                    crear_evento(
                        "demo_movimiento",
                        id_vehiculo,
                        comando=mov["comando"],
                        codigo=mov["codigo"],
                        indice=indice,
                        total_movimientos=total,
                        orden=mov["orden"],
                        duracion_ms=mov["duracion_ms"],
                        pausa_ms=mov["pausa_ms"],
                        **base,
                    ),
                )
                if await self._esperar(mov["duracion_ms"], ejecucion.cancelar):
                    break
                if await self._esperar(mov["pausa_ms"], ejecucion.cancelar):
                    break

            tipo = "demo_cancelada" if ejecucion.cancelar.is_set() else "demo_fin"
            await self._gestor.difundir(id_vehiculo, crear_evento(tipo, id_vehiculo, **base))
        except Exception:
            # El detalle queda en el log del servidor, nunca en el mensaje al cliente.
            log.exception("Falló la DEMO %s del vehículo %s", ejecucion.id_demo, id_vehiculo)
            await self._gestor.difundir(
                id_vehiculo,
                crear_evento(
                    "demo_error",
                    id_vehiculo,
                    mensaje="La DEMO terminó por un error interno",
                    **base,
                ),
            )
        finally:
            if self._activas.get(id_vehiculo) is ejecucion:
                del self._activas[id_vehiculo]


# Instancia compartida por toda la aplicación.
runner = DemoRunner()