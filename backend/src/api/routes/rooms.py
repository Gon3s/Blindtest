from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas.rooms import CreateRoomRequest, CreateRoomResponse
from src.application.room_service import RoomService
from src.infrastructure.db import get_db

router = APIRouter()


def get_room_service(session: Session = Depends(get_db)) -> RoomService:
    return RoomService(session)


@router.post("/rooms", response_model=CreateRoomResponse, status_code=201)
def create_room(
    payload: CreateRoomRequest,
    service: RoomService = Depends(get_room_service),
) -> CreateRoomResponse:
    result = service.create_room(payload.host_nickname)
    return CreateRoomResponse(
        room_id=result["room_id"],
        code=result["code"],
        host_id=result["host_id"],
    )
