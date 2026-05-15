from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.infrastructure.db import get_db
from src.infrastructure.models import ParticipantModel
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager

router = APIRouter()


@router.websocket("/ws/rooms/{room_id}")
async def websocket_room(
    websocket: WebSocket,
    room_id: UUID,
    db: Session = Depends(get_db),
    manager: RoomConnectionManager = Depends(get_ws_manager),
) -> None:
    await manager.connect(room_id, websocket)
    try:
        participants = (
            db.query(ParticipantModel).filter_by(room_id=room_id).all()
        )
        await websocket.send_json(
            {
                "event": "room.state",
                "data": {
                    "room_id": str(room_id),
                    "participants": [
                        {
                            "participant_id": str(p.id),
                            "nickname": p.nickname,
                            "is_host": p.is_host,
                        }
                        for p in participants
                    ],
                },
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
