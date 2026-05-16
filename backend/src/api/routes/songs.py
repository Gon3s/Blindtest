import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from src.api.routes.rooms import get_room_service
from src.api.schemas.songs import (
    StartSongResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from src.application.room_service import RoomService
from src.domain.exceptions import (
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotAcceptingAnswersError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotPlayableError,
)
from src.infrastructure.db import get_session_factory
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager

router = APIRouter()

SleepFn = Callable[[float], Awaitable[None]]


async def _default_sleep(delay: float) -> None:
    await asyncio.sleep(delay)


def get_sleep() -> SleepFn:
    return _default_sleep


def get_db_factory() -> sessionmaker[Session]:
    return get_session_factory()


async def _auto_lock_song(
    song_id: UUID,
    room_id: UUID,
    delay: float,
    session_factory: sessionmaker[Session],
    manager: RoomConnectionManager,
    sleep_fn: SleepFn,
) -> None:
    await sleep_fn(delay)
    session = session_factory()
    try:
        service = RoomService(session)
        result = service.lock_song(song_id)
        session.commit()
    except (SongNotFoundError, SongNotLockableError):
        session.rollback()
        return
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    await manager.broadcast_to_room(
        room_id,
        {
            "event": "song.locked",
            "data": {
                "song_id": str(result["song_id"]),
                "round_id": str(result["round_id"]),
            },
        },
    )


@router.post(
    "/rounds/{round_id}/songs/{song_index}/start",
    response_model=StartSongResponse,
    status_code=200,
)
async def start_song(
    round_id: UUID,
    song_index: int,
    background_tasks: BackgroundTasks,
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
    session_factory: sessionmaker[Session] = Depends(get_db_factory),
    sleep_fn: SleepFn = Depends(get_sleep),
) -> StartSongResponse:
    try:
        result = service.start_song(round_id, song_index)
    except RoundNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RoundNotInProgressError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SongNotPlayableError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "song.started",
            "data": {
                "song_id": str(result["song_id"]),
                "song_index": result["song_index"],
                "round_id": str(result["round_id"]),
                "started_at": result["started_at"].isoformat(),
                "ends_at": result["ends_at"].isoformat(),
            },
        },
    )

    delay = (result["ends_at"] - result["started_at"]).total_seconds()
    background_tasks.add_task(
        _auto_lock_song,
        result["song_id"],
        result["room_id"],
        delay,
        session_factory,
        manager,
        sleep_fn,
    )

    return StartSongResponse(
        song_id=result["song_id"],
        round_id=result["round_id"],
        room_id=result["room_id"],
        song_index=result["song_index"],
        started_at=result["started_at"],
        ends_at=result["ends_at"],
    )


@router.post(
    "/songs/{song_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=201,
)
async def submit_answer(
    song_id: UUID,
    body: SubmitAnswerRequest,
    service: RoomService = Depends(get_room_service),
) -> SubmitAnswerResponse:
    try:
        result = service.submit_answer(song_id, body.participant_id, body.text)
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SongNotAcceptingAnswersError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return SubmitAnswerResponse(
        answer_id=result["answer_id"],
        submitted_at=result["submitted_at"],
        validation_status=result["validation_status"],
        title_found=result["title_found"],
        artist_found=result["artist_found"],
    )
