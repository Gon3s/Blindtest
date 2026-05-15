from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.rooms import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    StartRoundRequest,
    StartRoundResponse,
)
from src.application.room_service import RoomService
from src.domain.exceptions import (
    NicknameAlreadyTakenError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
)
from src.domain.music_provider import MusicProvider
from src.infrastructure.db import get_db
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager

router = APIRouter()


def get_room_service(session: Session = Depends(get_db)) -> RoomService:
    return RoomService(session)


def get_music_provider() -> MusicProvider:
    return StaticFixtureMusicProvider()


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


@router.post("/rooms/{code}/join", response_model=JoinRoomResponse, status_code=201)
async def join_room(
    code: str,
    payload: JoinRoomRequest,
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
) -> JoinRoomResponse:
    try:
        result = service.join_room(code, payload.nickname)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (RoomNotJoinableError, NicknameAlreadyTakenError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "participant.joined",
            "data": {
                "participant_id": str(result["participant_id"]),
                "nickname": payload.nickname,
                "is_host": False,
            },
        },
    )
    return JoinRoomResponse(
        room_id=result["room_id"],
        participant_id=result["participant_id"],
    )


@router.post(
    "/rooms/{room_id}/rounds", response_model=StartRoundResponse, status_code=201
)
async def start_round(
    room_id: UUID,
    payload: StartRoundRequest,
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
    music_provider: MusicProvider = Depends(get_music_provider),
) -> StartRoundResponse:
    try:
        result = service.start_round(room_id, payload.theme, music_provider)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RoomNotWaitingError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "round.started",
            "data": {
                "round_id": str(result["round_id"]),
                "theme": result["theme"],
                "song_count": result["song_count"],
            },
        },
    )
    return StartRoundResponse(
        round_id=result["round_id"],
        room_id=result["room_id"],
        song_count=result["song_count"],
        theme=result["theme"],
    )
