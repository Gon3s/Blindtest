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
from src.api.schemas.songs import (
    AnswerSummaryItem,
    OverrideAnswerRequest,
    OverrideAnswerResponse,
    SongSummaryResponse,
    StartSongResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from src.application.room_service import RoomService
from src.domain.exceptions import (
    AnswerNotFoundError,
    NotHostError,
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotAcceptingAnswersError,
    SongNotCorrectableError,
    SongNotFoundError,
    SongNotLockedError,
    SongNotPlayableError,
)
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager

router = APIRouter()


@router.post(
    "/rounds/{round_id}/songs/{song_index}/start",
    response_model=StartSongResponse,
    status_code=200,
)
async def start_song(
    round_id: UUID,
    song_index: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
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

    db.commit()

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
        auto_lock_song,
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


@router.patch(
    "/songs/{song_id}/answers/{answer_id}",
    response_model=OverrideAnswerResponse,
    status_code=200,
)
def override_answer(
    song_id: UUID,
    answer_id: UUID,
    body: OverrideAnswerRequest,
    service: RoomService = Depends(get_room_service),
) -> OverrideAnswerResponse:
    try:
        result = service.override_answer(
            song_id,
            answer_id,
            body.host_id,
            body.title_accepted,
            body.artist_accepted,
        )
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AnswerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SongNotCorrectableError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except NotHostError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return OverrideAnswerResponse(
        answer_id=result["answer_id"],
        title_found=result["title_found"],
        artist_found=result["artist_found"],
        validation_status=result["validation_status"],
        score=result["score"],
    )


@router.get(
    "/songs/{song_id}/summary",
    response_model=SongSummaryResponse,
    status_code=200,
)
def get_song_summary(
    song_id: UUID,
    host_id: UUID,
    service: RoomService = Depends(get_room_service),
) -> SongSummaryResponse:
    try:
        result = service.get_song_summary(song_id, host_id)
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SongNotLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except NotHostError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return SongSummaryResponse(
        song_id=result["song_id"],
        title=result["title"],
        artist=result["artist"],
        total_answers=result["total_answers"],
        doubtful_count=result["doubtful_count"],
        answers=[AnswerSummaryItem(**item) for item in result["answers"]],
    )
