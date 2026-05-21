import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import RoundStatus, SongStatus, ValidationStatus
from src.domain.exceptions import (
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotAcceptingAnswersError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotPlayableError,
)
from src.infrastructure.models import AnswerModel, RoomModel, RoundModel, SongModel


class FakeClock:
    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


_FIXED_NOW = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
_DURATION = 30


def _make_song_mock(
    status: str = SongStatus.UPCOMING.value,
    round_id: UUID | None = None,
) -> MagicMock:
    song = MagicMock(spec=SongModel)
    song.id = uuid4()
    song.round_id = round_id or uuid4()
    song.status = status
    song.started_at = None
    song.ends_at = None
    return song


def _make_round_mock(
    status: str = RoundStatus.IN_PROGRESS.value,
    room_id: UUID | None = None,
) -> MagicMock:
    round_ = MagicMock(spec=RoundModel)
    round_.id = uuid4()
    round_.room_id = room_id or uuid4()
    round_.status = status
    return round_


def _session_for(round_: MagicMock, song: MagicMock) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is SongModel:
            q.filter_by.return_value.first.return_value = song
        return q

    mock.query.side_effect = _query
    return mock


# ── start_song ────────────────────────────────────────────────────────────────


@pytest.fixture
def round_id() -> UUID:
    return uuid4()


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def round_(round_id: UUID, room_id: UUID) -> MagicMock:
    r = _make_round_mock()
    r.id = round_id
    r.room_id = room_id
    return r


@pytest.fixture
def song(round_id: UUID) -> MagicMock:
    return _make_song_mock(round_id=round_id)


@pytest.fixture
def session(round_: MagicMock, song: MagicMock) -> MagicMock:
    return _session_for(round_, song)


@pytest.fixture
def service(session: MagicMock) -> RoomService:
    return RoomService(session, clock=FakeClock(_FIXED_NOW))


def test_start_song_sets_status_to_playing(
    service: RoomService, song: MagicMock, round_: MagicMock
) -> None:
    service.start_song(round_.id, song_index=0)
    assert song.status == SongStatus.PLAYING.value


def test_start_song_sets_started_at(
    service: RoomService, song: MagicMock, round_: MagicMock
) -> None:
    service.start_song(round_.id, song_index=0)
    assert song.started_at == _FIXED_NOW


def test_start_song_sets_ends_at_30s_later(
    service: RoomService, song: MagicMock, round_: MagicMock
) -> None:
    service.start_song(round_.id, song_index=0)
    assert song.ends_at == _FIXED_NOW + timedelta(seconds=_DURATION)


def test_start_song_returns_correct_ids(
    service: RoomService, round_: MagicMock, room_id: UUID
) -> None:
    result = service.start_song(round_.id, song_index=0)
    assert result["round_id"] == round_.id
    assert result["room_id"] == room_id
    assert isinstance(result["song_id"], UUID)


def test_start_song_returns_timestamps(service: RoomService, round_: MagicMock) -> None:
    result = service.start_song(round_.id, song_index=0)
    assert result["started_at"] == _FIXED_NOW
    assert result["ends_at"] == _FIXED_NOW + timedelta(seconds=_DURATION)


def test_start_song_returns_song_index(service: RoomService, round_: MagicMock) -> None:
    result = service.start_song(round_.id, song_index=3)
    assert result["song_index"] == 3


def test_start_song_uses_config_answer_duration(round_id: UUID, room_id: UUID) -> None:
    song = _make_song_mock(round_id=round_id)
    round_ = _make_round_mock(room_id=room_id)
    round_.id = round_id

    room = MagicMock()
    room.config = {"answer_duration_seconds": 45}

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        return q

    mock = MagicMock()
    mock.query.side_effect = _query
    svc = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = svc.start_song(round_id, song_index=0)
    assert result["ends_at"] == _FIXED_NOW + timedelta(seconds=45)


def test_start_song_round_not_found_raises() -> None:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(RoundNotFoundError):
        service.start_song(uuid4(), song_index=0)


def test_start_song_round_not_in_progress_raises() -> None:
    round_ = _make_round_mock(status=RoundStatus.FINISHED.value)
    song = _make_song_mock(round_id=round_.id)
    mock = _session_for(round_, song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(RoundNotInProgressError):
        service.start_song(round_.id, song_index=0)


def test_start_song_song_not_found_raises() -> None:
    round_ = _make_round_mock()
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(SongNotFoundError):
        service.start_song(round_.id, song_index=99)


def test_start_song_already_playing_raises(round_: MagicMock, room_id: UUID) -> None:
    song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_.id)
    mock = _session_for(round_, song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(SongNotPlayableError):
        service.start_song(round_.id, song_index=0)


# ── lock_song ─────────────────────────────────────────────────────────────────


def _session_for_lock(song: MagicMock, round_: MagicMock) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        return q

    mock.query.side_effect = _query
    return mock


def test_lock_song_sets_status_to_locked() -> None:
    round_ = _make_round_mock()
    song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_.id)
    mock = _session_for_lock(song, round_)
    service = RoomService(mock)
    service.lock_song(song.id)
    assert song.status == SongStatus.LOCKED.value


def test_lock_song_returns_correct_ids() -> None:
    round_ = _make_round_mock()
    room_id = round_.room_id
    song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_.id)
    mock = _session_for_lock(song, round_)
    service = RoomService(mock)
    result = service.lock_song(song.id)
    assert result["song_id"] == song.id
    assert result["round_id"] == song.round_id
    assert result["room_id"] == room_id


def test_lock_song_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    service = RoomService(mock)
    with pytest.raises(SongNotFoundError):
        service.lock_song(uuid4())


def test_lock_song_already_locked_raises() -> None:
    round_ = _make_round_mock()
    song = _make_song_mock(status=SongStatus.LOCKED.value, round_id=round_.id)
    mock = _session_for_lock(song, round_)
    service = RoomService(mock)
    with pytest.raises(SongNotLockableError):
        service.lock_song(song.id)


def test_lock_song_upcoming_raises() -> None:
    round_ = _make_round_mock()
    song = _make_song_mock(status=SongStatus.UPCOMING.value, round_id=round_.id)
    mock = _session_for_lock(song, round_)
    service = RoomService(mock)
    with pytest.raises(SongNotLockableError):
        service.lock_song(song.id)


# ── _auto_lock_song background task ───────────────────────────────────────────


def test_auto_lock_sleeps_for_delay_and_broadcasts() -> None:
    from unittest.mock import AsyncMock

    from src.api.deps import auto_lock_song as _auto_lock_song

    song_id = uuid4()
    round_id = uuid4()
    room_id = uuid4()

    playing_song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_id)
    playing_song.id = song_id
    lock_round = _make_round_mock()
    lock_round.id = round_id
    lock_round.room_id = room_id

    mock_session = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = playing_song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = lock_round
        return q

    mock_session.query.side_effect = _query

    mock_factory = MagicMock(return_value=mock_session)
    mock_manager = MagicMock()
    mock_manager.broadcast_to_room = AsyncMock()

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    asyncio.run(
        _auto_lock_song(
            song_id=song_id,
            room_id=room_id,
            delay=30.0,
            session_factory=mock_factory,
            manager=mock_manager,
            sleep_fn=fake_sleep,
        )
    )

    assert sleep_calls == [30.0]
    events = [c.args[1]["event"] for c in mock_manager.broadcast_to_room.call_args_list]
    assert "song.revealed" in events
    assert "song.locked" not in events
    revealed_call = next(
        c for c in mock_manager.broadcast_to_room.call_args_list
        if c.args[1]["event"] == "song.revealed"
    )
    assert revealed_call.args[0] == room_id
    assert revealed_call.args[1]["data"]["song_id"] == str(song_id)


def test_auto_lock_song_locked_status_after_run() -> None:
    from unittest.mock import AsyncMock

    from src.api.deps import auto_lock_song as _auto_lock_song

    song_id = uuid4()
    round_id = uuid4()
    room_id = uuid4()

    playing_song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_id)
    playing_song.id = song_id
    lock_round = _make_round_mock()
    lock_round.id = round_id
    lock_round.room_id = room_id

    mock_session = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = playing_song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = lock_round
        return q

    mock_session.query.side_effect = _query
    mock_factory = MagicMock(return_value=mock_session)
    mock_manager = MagicMock()
    mock_manager.broadcast_to_room = AsyncMock()

    async def instant(delay: float) -> None:
        pass

    asyncio.run(
        _auto_lock_song(
            song_id=song_id,
            room_id=room_id,
            delay=30.0,
            session_factory=mock_factory,
            manager=mock_manager,
            sleep_fn=instant,
        )
    )

    assert playing_song.status == SongStatus.REVEALED.value


def test_auto_lock_song_broadcasts_song_revealed() -> None:
    from unittest.mock import AsyncMock

    from src.api.deps import auto_lock_song as _auto_lock_song

    song_id = uuid4()
    round_id = uuid4()
    room_id = uuid4()

    playing_song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_id)
    playing_song.id = song_id
    lock_round = _make_round_mock()
    lock_round.id = round_id
    lock_round.room_id = room_id

    mock_session = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = playing_song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = lock_round
        return q

    mock_session.query.side_effect = _query
    mock_factory = MagicMock(return_value=mock_session)
    mock_manager = MagicMock()
    mock_manager.broadcast_to_room = AsyncMock()

    async def instant(delay: float) -> None:
        pass

    asyncio.run(
        _auto_lock_song(
            song_id=song_id,
            room_id=room_id,
            delay=0.0,
            session_factory=mock_factory,
            manager=mock_manager,
            sleep_fn=instant,
        )
    )

    events = [c.args[1]["event"] for c in mock_manager.broadcast_to_room.call_args_list]
    assert "song.revealed" in events


def test_auto_lock_song_does_not_broadcast_song_locked() -> None:
    from unittest.mock import AsyncMock

    from src.api.deps import auto_lock_song as _auto_lock_song

    song_id = uuid4()
    round_id = uuid4()
    room_id = uuid4()

    playing_song = _make_song_mock(status=SongStatus.PLAYING.value, round_id=round_id)
    playing_song.id = song_id
    lock_round = _make_round_mock()
    lock_round.id = round_id
    lock_round.room_id = room_id

    mock_session = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = playing_song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = lock_round
        return q

    mock_session.query.side_effect = _query
    mock_factory = MagicMock(return_value=mock_session)
    mock_manager = MagicMock()
    mock_manager.broadcast_to_room = AsyncMock()

    async def instant(delay: float) -> None:
        pass

    asyncio.run(
        _auto_lock_song(
            song_id=song_id,
            room_id=room_id,
            delay=0.0,
            session_factory=mock_factory,
            manager=mock_manager,
            sleep_fn=instant,
        )
    )

    events = [c.args[1]["event"] for c in mock_manager.broadcast_to_room.call_args_list]
    assert "song.locked" not in events


# ── submit_answer ──────────────────────────────────────────────────────────────


def _make_playing_song() -> MagicMock:
    song = MagicMock(spec=SongModel)
    song.id = uuid4()
    song.round_id = uuid4()
    song.status = SongStatus.PLAYING.value
    song.title = "One More Time"
    song.artist = "Daft Punk"
    song.aliases_title = []
    song.aliases_artist = []
    return song


def _session_for_answer(song: MagicMock) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    return mock


def _make_existing_answer(song_id: UUID, participant_id: UUID) -> MagicMock:
    a = MagicMock(spec=AnswerModel)
    a.id = uuid4()
    a.song_id = song_id
    a.participant_id = participant_id
    a.text = "old text"
    a.submitted_at = _FIXED_NOW - timedelta(seconds=5)
    a.title_found = False
    a.artist_found = False
    a.validation_status = ValidationStatus.NOT_FOUND.value
    a.host_override = None
    return a


def _session_for_answer_upsert(
    song: MagicMock, existing: MagicMock | None
) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is AnswerModel:
            q.filter_by.return_value.first.return_value = existing
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    return mock


def test_submit_answer_song_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(SongNotFoundError):
        service.submit_answer(uuid4(), uuid4(), "Daft Punk")


def test_submit_answer_song_not_playing_raises() -> None:
    song = _make_playing_song()
    song.status = SongStatus.LOCKED.value
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    with pytest.raises(SongNotAcceptingAnswersError):
        service.submit_answer(song.id, uuid4(), "Daft Punk")


def test_submit_answer_returns_answer_id() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, uuid4(), "Daft Punk")
    assert isinstance(result["answer_id"], UUID)


def test_submit_answer_submitted_at_from_clock() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, uuid4(), "Daft Punk")
    assert result["submitted_at"] == _FIXED_NOW


def test_submit_answer_title_found_on_exact_match() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, uuid4(), "one more time")
    assert result["title_found"] is True
    assert result["artist_found"] is False


def test_submit_answer_validation_status_found_on_any_exact() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, uuid4(), "daft punk")
    assert result["validation_status"] == ValidationStatus.FOUND.value


def test_submit_answer_validation_status_not_found_on_wrong_answer() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, uuid4(), "around the world foo bar baz")
    assert result["validation_status"] == ValidationStatus.NOT_FOUND.value
    assert result["title_found"] is False
    assert result["artist_found"] is False


def test_submit_answer_validation_status_doubtful_on_fuzzy_title() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    # "one more tyme" is close to "One More Time" (fuzzy ≥ 0.75) but not exact
    result = service.submit_answer(song.id, uuid4(), "one more tyme")
    assert result["validation_status"] == ValidationStatus.DOUBTFUL.value
    assert result["title_found"] is False
    assert result["artist_found"] is False


def test_submit_answer_validation_status_doubtful_on_fuzzy_artist() -> None:
    song = _make_playing_song()
    mock = _session_for_answer(song)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    # "daff punk" is close to "Daft Punk" (fuzzy ratio ~0.89 ≥ 0.75) but not exact
    result = service.submit_answer(song.id, uuid4(), "daff punk")
    assert result["validation_status"] == ValidationStatus.DOUBTFUL.value
    assert result["title_found"] is False
    assert result["artist_found"] is False


# ── submit_answer upsert ───────────────────────────────────────────────────────


def test_submit_answer_first_submission_inserts_new_row() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    mock = _session_for_answer_upsert(song, None)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, participant_id, "daft punk")
    mock.add.assert_called_once()
    assert isinstance(result["answer_id"], UUID)


def test_submit_answer_second_submission_returns_same_answer_id() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, participant_id, "daft punk")
    assert result["answer_id"] == existing.id


def test_submit_answer_second_submission_does_not_add_new_row() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    service.submit_answer(song.id, participant_id, "daft punk")
    mock.add.assert_not_called()


def test_submit_answer_second_submission_updates_text() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    service.submit_answer(song.id, participant_id, "One More Time")
    assert existing.text == "One More Time"


def test_submit_answer_second_submission_updates_submitted_at() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    service.submit_answer(song.id, participant_id, "daft punk")
    assert existing.submitted_at == _FIXED_NOW


def test_submit_answer_second_submission_updates_validation() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    result = service.submit_answer(song.id, participant_id, "daft punk")
    assert existing.artist_found is True
    assert existing.validation_status == ValidationStatus.FOUND.value
    assert result["artist_found"] is True


def test_submit_answer_second_submission_resets_host_override() -> None:
    song = _make_playing_song()
    participant_id = uuid4()
    existing = _make_existing_answer(song.id, participant_id)
    existing.host_override = ValidationStatus.FOUND.value
    mock = _session_for_answer_upsert(song, existing)
    service = RoomService(mock, clock=FakeClock(_FIXED_NOW))
    service.submit_answer(song.id, participant_id, "totally wrong answer zzz")
    assert existing.host_override is None
