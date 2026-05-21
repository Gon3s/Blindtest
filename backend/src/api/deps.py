import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from src.application.room_service import RoomService
from src.domain.exceptions import (
    RoomNotFoundError,
    RoundNotFoundError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotRevealableError,
)
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
        service.lock_song(song_id)
        reveal_result = service.reveal_song_auto(song_id)
        session.commit()
    except (
        SongNotFoundError,
        SongNotLockableError,
        SongNotRevealableError,
        RoundNotFoundError,
        RoomNotFoundError,
    ):
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
            "event": "song.revealed",
            "data": {
                "song_id": str(reveal_result["song_id"]),
                "title": reveal_result["title"],
                "artist": reveal_result["artist"],
                "player_results": [
                    {
                        "participant_id": str(pr["participant_id"]),
                        "nickname": pr["nickname"],
                        "answer": pr["answer"],
                        "title_found": pr["title_found"],
                        "artist_found": pr["artist_found"],
                        "score": pr["score"],
                    }
                    for pr in reveal_result["player_results"]
                ],
                "mini_leaderboard": [
                    {
                        "rank": lb["rank"],
                        "participant_id": str(lb["participant_id"]),
                        "nickname": lb["nickname"],
                        "total_points": lb["total_points"],
                    }
                    for lb in reveal_result["mini_leaderboard"]
                ],
            },
        },
    )
    if reveal_result["round_finished"]:
        await manager.broadcast_to_room(
            room_id,
            {
                "event": "round.finished",
                "data": {
                    "room_id": str(room_id),
                    "round_leaderboard": [
                        {
                            "rank": lb["rank"],
                            "participant_id": str(lb["participant_id"]),
                            "nickname": lb["nickname"],
                            "round_points": lb["round_points"],
                        }
                        for lb in reveal_result["round_leaderboard"]
                    ],
                },
            },
        )
