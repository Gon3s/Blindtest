from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
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
    MiniLeaderboardItem,
    OverrideAnswerRequest,
    OverrideAnswerResponse,
    PlayerRevealItem,
    RevealSongRequest,
    RevealSongResponse,
    RoundLeaderboardItem,
    SongSummaryRequest,
    SongSummaryResponse,
    StartSongResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from src.application.room_service import RoomService
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
    result = service.start_song(round_id, song_index)

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
                "preview_url": result["preview_url"],
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
        preview_url=result["preview_url"],
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
    result = service.submit_answer(song_id, body.participant_id, body.text)

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
    result = service.override_answer(
        song_id,
        answer_id,
        body.host_token,
        body.title_accepted,
        body.artist_accepted,
    )

    return OverrideAnswerResponse(
        answer_id=result["answer_id"],
        title_found=result["title_found"],
        artist_found=result["artist_found"],
        validation_status=result["validation_status"],
        score=result["score"],
    )


@router.post(
    "/songs/{song_id}/summary",
    response_model=SongSummaryResponse,
    status_code=200,
)
def get_song_summary(
    song_id: UUID,
    body: SongSummaryRequest,
    service: RoomService = Depends(get_room_service),
) -> SongSummaryResponse:
    result = service.get_song_summary(song_id, body.host_token)

    return SongSummaryResponse(
        song_id=result["song_id"],
        title=result["title"],
        artist=result["artist"],
        total_answers=result["total_answers"],
        doubtful_count=result["doubtful_count"],
        answers=[AnswerSummaryItem(**item) for item in result["answers"]],
    )


@router.post(
    "/songs/{song_id}/reveal",
    response_model=RevealSongResponse,
    status_code=200,
)
async def reveal_song(
    song_id: UUID,
    body: RevealSongRequest,
    service: RoomService = Depends(get_room_service),
    manager: RoomConnectionManager = Depends(get_ws_manager),
) -> RevealSongResponse:
    result = service.reveal_song(song_id, body.host_token)

    await manager.broadcast_to_room(
        result["room_id"],
        {
            "event": "song.revealed",
            "data": {
                "song_id": str(result["song_id"]),
                "title": result["title"],
                "artist": result["artist"],
                "cover_url": result["cover_url"],
                "player_results": [
                    {
                        "participant_id": str(pr["participant_id"]),
                        "nickname": pr["nickname"],
                        "answer": pr["answer"],
                        "title_found": pr["title_found"],
                        "artist_found": pr["artist_found"],
                        "score": pr["score"],
                    }
                    for pr in result["player_results"]
                ],
                "mini_leaderboard": [
                    {
                        "rank": lb["rank"],
                        "participant_id": str(lb["participant_id"]),
                        "nickname": lb["nickname"],
                        "total_points": lb["total_points"],
                    }
                    for lb in result["mini_leaderboard"]
                ],
            },
        },
    )

    round_finished = result["round_finished"]
    round_leaderboard = result["round_leaderboard"]

    if round_finished:
        await manager.broadcast_to_room(
            result["room_id"],
            {
                "event": "round.finished",
                "data": {
                    "room_id": str(result["room_id"]),
                    "round_leaderboard": [
                        {
                            "rank": lb["rank"],
                            "participant_id": str(lb["participant_id"]),
                            "nickname": lb["nickname"],
                            "round_points": lb["round_points"],
                        }
                        for lb in round_leaderboard
                    ],
                },
            },
        )

    return RevealSongResponse(
        song_id=result["song_id"],
        room_id=result["room_id"],
        title=result["title"],
        artist=result["artist"],
        cover_url=result["cover_url"],
        player_results=[PlayerRevealItem(**pr) for pr in result["player_results"]],
        mini_leaderboard=[
            MiniLeaderboardItem(**lb) for lb in result["mini_leaderboard"]
        ],
        round_finished=round_finished,
        round_leaderboard=[RoundLeaderboardItem(**lb) for lb in round_leaderboard],
    )
