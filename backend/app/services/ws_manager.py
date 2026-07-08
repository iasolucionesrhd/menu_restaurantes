from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, restaurante_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(restaurante_id, set()).add(websocket)

    def disconnect(self, restaurante_id: int, websocket: WebSocket) -> None:
        conexiones = self._connections.get(restaurante_id)
        if conexiones:
            conexiones.discard(websocket)
            if not conexiones:
                del self._connections[restaurante_id]

    async def broadcast(self, restaurante_id: int, message: dict) -> None:
        conexiones = list(self._connections.get(restaurante_id, ()))
        for ws in conexiones:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(restaurante_id, ws)


manager = ConnectionManager()
