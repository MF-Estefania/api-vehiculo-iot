import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Administra los clientes WebSocket agrupados por vehículo.

    Un cliente solo recibe eventos del vehículo que está monitoreando.
    """

    def __init__(self) -> None:
        self._conexiones: dict[int, set[WebSocket]] = defaultdict(set)

    async def conectar(self, id_vehiculo: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conexiones[id_vehiculo].add(websocket)

    def desconectar(self, id_vehiculo: int, websocket: WebSocket) -> None:
        clientes = self._conexiones.get(id_vehiculo)
        if clientes is None:
            return
        clientes.discard(websocket)
        if not clientes:
            self._conexiones.pop(id_vehiculo, None)

    async def enviar(self, websocket: WebSocket, mensaje: dict) -> bool:
        """Envía a un cliente. Devuelve False si falló (cliente caído)."""
        try:
            await websocket.send_json(mensaje)
            return True
        except Exception:
            return False

    async def difundir(self, id_vehiculo: int, mensaje: dict) -> int:
        """Envía a todos los clientes del vehículo y devuelve cuántos lo recibieron."""
        destinatarios = list(self._conexiones.get(id_vehiculo, ()))
        if not destinatarios:
            return 0
        resultados = await asyncio.gather(
            *(self.enviar(ws, mensaje) for ws in destinatarios)
        )
        for websocket, recibido in zip(destinatarios, resultados):
            if not recibido:
                self.desconectar(id_vehiculo, websocket)
        return sum(resultados)


# Instancia compartida por toda la aplicación.
manager = ConnectionManager()