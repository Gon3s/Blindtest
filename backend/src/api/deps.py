import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from src.application.room_service import RoomService
from src.domain.exceptions import SongNotFoundError, SongNotLockableError
from src.infrastructure.db import get_db, get_session_factory
from src.infrastructure.ws_manager import RoomConnectionManager

SleepFn = Callable[[float], Awaitable[None]]


async def _default_sleep(delay: float) -> None:
    await asyncio.sleep(delay)


def get_sleep() -> SleepFn:
    return _default_sleep


def get_db_factory() -> sessionmaker[Session]:
    return get_session_factory()


def get_session(session: Session = Depends(get_db)) -> Session:
    return session


def get_room_service(session: Session = Depends(get_db)) -> RoomService:
    return RoomService(session)


async def auto_lock_song(
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
