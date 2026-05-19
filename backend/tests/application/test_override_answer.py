from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import SongStatus, ValidationStatus
from src.domain.exceptions import (
    AnswerNotFoundError,
    NotHostError,
    SongNotCorrectableError,
    SongNotFoundError,
)
from src.infrastructure.models import (
    AnswerModel,
    RoomModel,
    RoundModel,
    ScoreEntryModel,
    SongModel,
)

_STARTED_AT = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
_ENDS_AT = _STARTED_AT + timedelta(seconds=30)
_SUBMITTED_AT = _STARTED_AT + timedelta(seconds=20)  # 10s remaining when submitted


def _make_locked_song(song_status: str = SongStatus.LOCKED.value) -> MagicMock:
    song = MagicMock(spec=SongModel)
    song.id = uuid4()
    song.round_id = uuid4()
    song.status = song_status
    song.title = "One More Time"
    song.artist = "Daft Punk"
    song.started_at = _STARTED_AT
    song.ends_at = _ENDS_AT
    return song


def _make_answer(
    song_id: UUID,
    title_found: bool = False,
    artist_found: bool = False,
) -> MagicMock:
    answer = MagicMock(spec=AnswerModel)
    answer.id = uuid4()
    answer.song_id = song_id
    answer.participant_id = uuid4()
    answer.text = "daft punk"
    answer.submitted_at = _SUBMITTED_AT
    answer.title_found = title_found
    answer.artist_found = artist_found
    answer.validation_status = ValidationStatus.NOT_FOUND.value
    answer.host_override = None
    return answer


_DEFAULT_HOST_TOKEN = "correct-host-token"


def _make_room(host_token: str | None = None) -> MagicMock:
    room = MagicMock(spec=RoomModel)
    room.id = uuid4()
    room.host_token = host_token or _DEFAULT_HOST_TOKEN
    return room


def _make_round(room_id: UUID, round_id: UUID) -> MagicMock:
    round_ = MagicMock(spec=RoundModel)
    round_.id = round_id
    round_.room_id = room_id
    return round_


def _session_for_override(
    song: MagicMock,
    round_: MagicMock,
    room: MagicMock,
    answer: MagicMock,
    score_entry: MagicMock | None = None,
) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        elif model is AnswerModel:
            q.filter_by.return_value.first.return_value = answer
        elif model is ScoreEntryModel:
            q.filter_by.return_value.first.return_value = score_entry
        return q

    mock.query.side_effect = _query
    return mock


def _make_full_context(
    host_token: str | None = None,
    song_status: str = SongStatus.LOCKED.value,
    title_found: bool = False,
    artist_found: bool = False,
    score_entry: MagicMock | None = None,
) -> tuple[MagicMock, MagicMock, str, MagicMock]:
    effective_host_token = host_token or _DEFAULT_HOST_TOKEN
    song = _make_locked_song(song_status)
    room = _make_room(host_token=effective_host_token)
    round_ = _make_round(room_id=room.id, round_id=song.round_id)
    answer = _make_answer(song.id, title_found=title_found, artist_found=artist_found)
    session = _session_for_override(song, round_, room, answer, score_entry)
    return session, answer, effective_host_token, song


# ── 1. accepter titre ─────────────────────────────────────────────────────────


def test_override_accept_title_sets_title_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=False
    )

    assert answer.title_found is True
    assert answer.artist_found is False
    assert result["title_found"] is True
    assert result["artist_found"] is False


def test_override_accept_title_validation_status_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=False
    )

    assert result["validation_status"] == ValidationStatus.FOUND.value


# ── 2. accepter artiste ───────────────────────────────────────────────────────


def test_override_accept_artist_sets_artist_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=True
    )

    assert answer.title_found is False
    assert answer.artist_found is True
    assert result["title_found"] is False
    assert result["artist_found"] is True


def test_override_accept_artist_validation_status_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=True
    )

    assert result["validation_status"] == ValidationStatus.FOUND.value


# ── 3. tout accepter ──────────────────────────────────────────────────────────


def test_override_accept_both_sets_both_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=True
    )

    assert answer.title_found is True
    assert answer.artist_found is True
    assert result["title_found"] is True
    assert result["artist_found"] is True


def test_override_accept_both_validation_status_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=True
    )

    assert result["validation_status"] == ValidationStatus.FOUND.value


# ── 4. refuser ────────────────────────────────────────────────────────────────


def test_override_reject_sets_both_not_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=False
    )

    assert answer.title_found is False
    assert answer.artist_found is False
    assert result["title_found"] is False
    assert result["artist_found"] is False


def test_override_reject_validation_status_not_found() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=False
    )

    assert result["validation_status"] == ValidationStatus.NOT_FOUND.value


# ── 5. correction écrase validation automatique ───────────────────────────────


def test_override_erases_auto_title_found() -> None:
    # Auto-validation set title_found=True; host overrides to False
    session, answer, host_token, song = _make_full_context(
        title_found=True, artist_found=False
    )
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=False
    )

    assert answer.title_found is False
    assert result["title_found"] is False


def test_override_erases_auto_artist_found() -> None:
    session, answer, host_token, song = _make_full_context(
        title_found=False, artist_found=True
    )
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=False
    )

    assert answer.artist_found is False
    assert result["artist_found"] is False


def test_override_host_override_field_set() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=False
    )

    assert answer.host_override is not None


# ── 6. recalcul score ─────────────────────────────────────────────────────────


def test_override_score_both_accepted_is_correct() -> None:
    # started_at=T, ends_at=T+30s, submitted_at=T+20s → 10s remaining
    # score = 100 + 100 + 50 (combo) + round(10/30 * 50) = 250 + 17 = 267
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=True
    )

    assert result["score"] == 267


def test_override_score_title_only_is_correct() -> None:
    # base=100, speed_bonus=round(10/30*50)=17 → 117
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=False
    )

    assert result["score"] == 117


def test_override_score_rejected_is_zero() -> None:
    session, answer, host_token, song = _make_full_context()
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=False
    )

    assert result["score"] == 0


def test_override_creates_score_entry_when_none_exists() -> None:
    session, answer, host_token, song = _make_full_context(score_entry=None)
    service = RoomService(session)

    service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=True
    )

    session.add.assert_called()


def test_override_updates_existing_score_entry() -> None:
    existing = MagicMock(spec=ScoreEntryModel)
    existing.points = 0
    session, answer, host_token, song = _make_full_context(score_entry=existing)
    service = RoomService(session)

    service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=True
    )

    assert existing.points == 267


# ── erreurs ───────────────────────────────────────────────────────────────────


def test_override_song_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    service = RoomService(mock)

    with pytest.raises(SongNotFoundError):
        service.override_answer(uuid4(), uuid4(), "any-token", True, False)


def test_override_song_playing_raises_not_correctable() -> None:
    song = _make_locked_song(song_status=SongStatus.PLAYING.value)
    room = _make_room()
    round_ = _make_round(room_id=room.id, round_id=song.round_id)
    answer = _make_answer(song.id)
    session = _session_for_override(song, round_, room, answer)
    service = RoomService(session)

    with pytest.raises(SongNotCorrectableError):
        service.override_answer(song.id, answer.id, room.host_token, True, False)


def test_override_song_scored_raises_not_correctable() -> None:
    song = _make_locked_song(song_status=SongStatus.SCORED.value)
    room = _make_room()
    round_ = _make_round(room_id=room.id, round_id=song.round_id)
    answer = _make_answer(song.id)
    session = _session_for_override(song, round_, room, answer)
    service = RoomService(session)

    with pytest.raises(SongNotCorrectableError):
        service.override_answer(song.id, answer.id, room.host_token, True, False)


def test_override_not_host_raises() -> None:
    session, answer, _, song = _make_full_context(host_token="correct-token")
    service = RoomService(session)

    with pytest.raises(NotHostError):
        service.override_answer(song.id, answer.id, "wrong-token", True, False)


def test_override_answer_not_found_raises() -> None:
    song = _make_locked_song()
    room = _make_room(host_token="correct-token")
    round_ = _make_round(room_id=room.id, round_id=song.round_id)

    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    service = RoomService(mock)

    with pytest.raises(AnswerNotFoundError):
        service.override_answer(song.id, uuid4(), "correct-token", True, False)


def test_override_validation_allowed_when_song_in_validation_state() -> None:
    session, answer, host_token, song = _make_full_context(
        song_status=SongStatus.VALIDATION.value
    )
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=True, artist_accepted=False
    )

    assert result["title_found"] is True


def test_override_allowed_when_song_in_revealed_state() -> None:
    session, answer, host_token, song = _make_full_context(
        song_status=SongStatus.REVEALED.value
    )
    service = RoomService(session)

    result = service.override_answer(
        song.id, answer.id, host_token, title_accepted=False, artist_accepted=True
    )

    assert result["artist_found"] is True
