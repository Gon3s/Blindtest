from typing import Any
from uuid import UUID

from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = {}

    async def connect(self, room_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(room_id, set()).add(websocket)

    def disconnect(self, room_id: UUID, websocket: WebSocket) -> None:
        room_connections = self._connections.get(room_id)
        if room_connections:
            room_connections.discard(websocket)
            if not room_connections:
                del self._connections[room_id]

    async def broadcast_to_room(
        self, room_id: UUID, message: dict[str, Any]
    ) -> None:
        for websocket in list(self._connections.get(room_id, set())):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(room_id, websocket)


_manager = RoomConnectionManager()


def get_ws_manager() -> RoomConnectionManager:
    return _manager
