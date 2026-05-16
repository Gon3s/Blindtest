from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from src.api.deps import (
    SleepFn,
    auto_lock_song,
    get_db_factory,
    get_room_service,
    get_session,
    get_sleep,
)
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
    RoomNotFinishedRoundError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
    SongNotFoundError,
    SongNotPlayableError,
)
from src.domain.music_provider import MusicProvider
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager

router = APIRouter()


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
    music_provider: MusicProvider = Depends(get_music_provider),
    session_factory: sessionmaker[Session] = Depends(get_db_factory),
    sleep_fn: SleepFn = Depends(get_sleep),
) -> StartRoundResponse:
    try:
        result = service.start_round(room_id, payload.theme, music_provider)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RoomNotWaitingError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    try:
        song_result = service.start_song(result["round_id"], 0)
    except (SongNotFoundError, SongNotPlayableError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    db.commit()

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
    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "song.started",
            "data": {
                "song_id": str(song_result["song_id"]),
                "song_index": song_result["song_index"],
                "round_id": str(song_result["round_id"]),
                "started_at": song_result["started_at"].isoformat(),
                "ends_at": song_result["ends_at"].isoformat(),
            },
        },
    )

    delay = (song_result["ends_at"] - song_result["started_at"]).total_seconds()
    background_tasks.add_task(
        auto_lock_song,
        song_result["song_id"],
        result["room_id"],
        delay,
        session_factory,
        manager,
        sleep_fn,
    )

    return StartRoundResponse(
        round_id=result["round_id"],
        room_id=result["room_id"],
        song_count=result["song_count"],
        theme=result["theme"],
    )


@router.post(
    "/rooms/{room_id}/restart", response_model=StartRoundResponse, status_code=201
)
async def restart_round(
    room_id: UUID,
    payload: StartRoundRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
    music_provider: MusicProvider = Depends(get_music_provider),
    session_factory: sessionmaker[Session] = Depends(get_db_factory),
    sleep_fn: SleepFn = Depends(get_sleep),
) -> StartRoundResponse:
    try:
        result = service.restart_round(room_id, payload.theme, music_provider)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RoomNotFinishedRoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    try:
        song_result = service.start_song(result["round_id"], 0)
    except (SongNotFoundError, SongNotPlayableError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    db.commit()

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
    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "song.started",
            "data": {
                "song_id": str(song_result["song_id"]),
                "song_index": song_result["song_index"],
                "round_id": str(song_result["round_id"]),
                "started_at": song_result["started_at"].isoformat(),
                "ends_at": song_result["ends_at"].isoformat(),
            },
        },
    )

    delay = (song_result["ends_at"] - song_result["started_at"]).total_seconds()
    background_tasks.add_task(
        auto_lock_song,
        song_result["song_id"],
        result["room_id"],
        delay,
        session_factory,
        manager,
        sleep_fn,
    )

    return StartRoundResponse(
        round_id=result["round_id"],
        room_id=result["room_id"],
        song_count=result["song_count"],
        theme=result["theme"],
    )
