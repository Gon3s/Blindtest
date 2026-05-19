"""TDD — get_song_summary service method (T-029)."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import SongStatus, ValidationStatus
from src.domain.exceptions import (
    NotHostError,
    SongNotFoundError,
    SongNotLockedError,
)
from src.infrastructure.models import (
    AnswerModel,
    ParticipantModel,
    RoomModel,
    RoundModel,
    SongModel,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _song(
    status: str = SongStatus.LOCKED.value,
    round_id: UUID | None = None,
) -> MagicMock:
    s = MagicMock(spec=SongModel)
    s.id = uuid4()
    s.round_id = round_id or uuid4()
    s.title = "One More Time"
    s.artist = "Daft Punk"
    s.status = status
    return s


def _round(room_id: UUID | None = None) -> MagicMock:
    r = MagicMock(spec=RoundModel)
    r.id = uuid4()
    r.room_id = room_id or uuid4()
    return r


def _room(host_token: str, room_id: UUID | None = None) -> MagicMock:
    r = MagicMock(spec=RoomModel)
    r.id = room_id or uuid4()
    r.host_token = host_token
    return r


def _answer(
    song_id: UUID,
    participant_id: UUID,
    text: str = "daft punk",
    validation_status: str = ValidationStatus.NOT_FOUND.value,
    title_found: bool = False,
    artist_found: bool = False,
) -> MagicMock:
    a = MagicMock(spec=AnswerModel)
    a.id = uuid4()
    a.song_id = song_id
    a.participant_id = participant_id
    a.text = text
    a.validation_status = validation_status
    a.title_found = title_found
    a.artist_found = artist_found
    return a


def _participant(pid: UUID, nickname: str) -> MagicMock:
    p = MagicMock(spec=ParticipantModel)
    p.id = pid
    p.nickname = nickname
    return p


def _session(
    song: MagicMock,
    round_: MagicMock,
    room: MagicMock,
    answers: list[MagicMock],
    participants: list[MagicMock],
) -> MagicMock:
    pmap = {p.id: p for p in participants}
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
            q.filter_by.return_value.all.return_value = answers
        elif model is ParticipantModel:

            def _fb(**kw: object) -> MagicMock:
                inner = MagicMock()
                inner.first.return_value = pmap.get(kw.get("id"))  # type: ignore[arg-type]
                return inner

            q.filter_by.side_effect = _fb
        return q

    mock.query.side_effect = _query
    return mock


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def host_token() -> str:
    return "summary-host-token"


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def locked_song() -> MagicMock:
    return _song(status=SongStatus.LOCKED.value)


@pytest.fixture
def participant_alice() -> tuple[UUID, MagicMock]:
    pid = uuid4()
    return pid, _participant(pid, "Alice")


@pytest.fixture
def participant_bob() -> tuple[UUID, MagicMock]:
    pid = uuid4()
    return pid, _participant(pid, "Bob")


# ── summary without doubtful answers ─────────────────────────────────────────


def test_summary_no_doubtful_returns_zero_doubtful_count(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(
        locked_song.id,
        alice_id,
        text="One More Time",
        validation_status=ValidationStatus.FOUND.value,
        title_found=True,
    )
    sess = _session(locked_song, round_, room, [ans], [alice])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    assert result["doubtful_count"] == 0
    assert result["total_answers"] == 1


def test_summary_not_found_answers_do_not_increment_doubtful(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(
        locked_song.id,
        alice_id,
        text="around the world",
        validation_status=ValidationStatus.NOT_FOUND.value,
    )
    sess = _session(locked_song, round_, room, [ans], [alice])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    assert result["doubtful_count"] == 0


# ── summary with doubtful answer ──────────────────────────────────────────────


def test_summary_doubtful_answer_increments_doubtful_count(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
    participant_bob: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    bob_id, bob = participant_bob
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    doubtful = _answer(
        locked_song.id,
        alice_id,
        text="one more tyme",
        validation_status=ValidationStatus.DOUBTFUL.value,
    )
    found = _answer(
        locked_song.id,
        bob_id,
        text="One More Time",
        validation_status=ValidationStatus.FOUND.value,
        title_found=True,
    )
    sess = _session(locked_song, round_, room, [doubtful, found], [alice, bob])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    assert result["doubtful_count"] == 1
    assert result["total_answers"] == 2


def test_summary_doubtful_answer_validation_status_in_list(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(
        locked_song.id,
        alice_id,
        text="one more tyme",
        validation_status=ValidationStatus.DOUBTFUL.value,
    )
    sess = _session(locked_song, round_, room, [ans], [alice])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    assert result["answers"][0]["validation_status"] == ValidationStatus.DOUBTFUL.value


# ── correct answer visible to host ────────────────────────────────────────────


def test_summary_returns_song_title_and_artist(
    host_token: str,
    room_id: UUID,
) -> None:
    song = _song()
    song.title = "Get Lucky"
    song.artist = "Daft Punk"
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(song, round_, room, [], [])
    result = RoomService(sess).get_song_summary(song.id, host_token)
    assert result["title"] == "Get Lucky"
    assert result["artist"] == "Daft Punk"


def test_summary_returns_song_id(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    assert result["song_id"] == locked_song.id


# ── raw answer text accessible ────────────────────────────────────────────────


def test_summary_answer_contains_raw_text_and_nickname(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(locked_song.id, alice_id, text="daft punk")
    sess = _session(locked_song, round_, room, [ans], [alice])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    item = result["answers"][0]
    assert item["text"] == "daft punk"
    assert item["nickname"] == "Alice"
    assert item["participant_id"] == alice_id


def test_summary_answer_contains_validation_flags(
    locked_song: MagicMock,
    host_token: str,
    room_id: UUID,
    participant_alice: tuple[UUID, MagicMock],
) -> None:
    alice_id, alice = participant_alice
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(
        locked_song.id,
        alice_id,
        text="One More Time",
        validation_status=ValidationStatus.FOUND.value,
        title_found=True,
        artist_found=False,
    )
    sess = _session(locked_song, round_, room, [ans], [alice])
    result = RoomService(sess).get_song_summary(locked_song.id, host_token)
    item = result["answers"][0]
    assert item["title_found"] is True
    assert item["artist_found"] is False
    assert item["validation_status"] == ValidationStatus.FOUND.value


# ── errors ────────────────────────────────────────────────────────────────────


def test_summary_song_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    with pytest.raises(SongNotFoundError):
        RoomService(mock).get_song_summary(uuid4(), "any-token")


def test_summary_song_still_playing_raises(host_token: str, room_id: UUID) -> None:
    playing = _song(status=SongStatus.PLAYING.value)
    round_ = _round(room_id=room_id)
    playing.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(playing, round_, room, [], [])
    with pytest.raises(SongNotLockedError):
        RoomService(sess).get_song_summary(playing.id, host_token)


def test_summary_song_upcoming_raises(host_token: str, room_id: UUID) -> None:
    upcoming = _song(status=SongStatus.UPCOMING.value)
    round_ = _round(room_id=room_id)
    upcoming.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(upcoming, round_, room, [], [])
    with pytest.raises(SongNotLockedError):
        RoomService(sess).get_song_summary(upcoming.id, host_token)


def test_summary_wrong_host_raises(room_id: UUID) -> None:
    song = _song()
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token="correct-token", room_id=room_id)
    sess = _session(song, round_, room, [], [])
    with pytest.raises(NotHostError):
        RoomService(sess).get_song_summary(song.id, "wrong-token")


def test_summary_accessible_for_later_statuses(host_token: str, room_id: UUID) -> None:
    for status in (
        SongStatus.VALIDATION.value,
        SongStatus.REVEALED.value,
        SongStatus.SCORED.value,
    ):
        song = _song(status=status)
        round_ = _round(room_id=room_id)
        song.round_id = round_.id
        room = _room(host_token=host_token, room_id=room_id)
        sess = _session(song, round_, room, [], [])
        result = RoomService(sess).get_song_summary(song.id, host_token)
        assert result["song_id"] == song.id
