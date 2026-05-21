"""Unit tests — RoomService.get_room_state (T-104)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import RoomStatus, SongStatus
from src.domain.exceptions import RoomNotFoundError
from src.infrastructure.models import (
    ParticipantModel,
    RoomModel,
    RoundModel,
    SongModel,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_room(status: str = RoomStatus.WAITING.value) -> MagicMock:
    r = MagicMock(spec=RoomModel)
    r.id = uuid4()
    r.code = "ABC123"
    r.status = status
    return r


def _make_participant(nickname: str, is_host: bool = False) -> MagicMock:
    p = MagicMock(spec=ParticipantModel)
    p.id = uuid4()
    p.nickname = nickname
    p.is_host = is_host
    return p


def _make_round(room_id: UUID) -> MagicMock:
    r = MagicMock(spec=RoundModel)
    r.id = uuid4()
    r.room_id = room_id
    return r


def _make_song(round_id: UUID, index: int = 0) -> MagicMock:
    s = MagicMock(spec=SongModel)
    s.id = uuid4()
    s.round_id = round_id
    s.index = index
    s.status = SongStatus.PLAYING.value
    s.ends_at = datetime(2026, 5, 21, 20, 0, 0, tzinfo=timezone.utc)
    s.preview_url = "https://example.com/preview.mp3"
    return s


def _make_session(
    room: MagicMock | None,
    participants: list[MagicMock],
    round_: MagicMock | None = None,
    current_song: MagicMock | None = None,
    total_songs: int = 0,
) -> MagicMock:
    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        elif model is ParticipantModel:
            q.filter_by.return_value.all.return_value = participants
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is SongModel:

            def _fb(**kw: object) -> MagicMock:
                inner = MagicMock()
                if "status" in kw:
                    inner.first.return_value = current_song
                else:
                    inner.count.return_value = total_songs
                return inner

            q.filter_by.side_effect = _fb
        return q

    mock.query.side_effect = _query
    return mock


# ── tests ─────────────────────────────────────────────────────────────────────


def test_get_room_state_raises_when_room_not_found() -> None:
    session = _make_session(room=None, participants=[])
    service = RoomService(session)
    with pytest.raises(RoomNotFoundError):
        service.get_room_state("XXXXXX")


def test_get_room_state_returns_room_id_and_code() -> None:
    room = _make_room()
    session = _make_session(room, participants=[])
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["room_id"] == room.id
    assert result["code"] == "ABC123"


def test_get_room_state_returns_status() -> None:
    room = _make_room(RoomStatus.WAITING.value)
    session = _make_session(room, participants=[])
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["status"] == RoomStatus.WAITING.value


def test_get_room_state_returns_participants() -> None:
    room = _make_room()
    participants = [
        _make_participant("Alice", is_host=True),
        _make_participant("Bob"),
    ]
    session = _make_session(room, participants)
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert len(result["participants"]) == 2
    nicknames = {p["nickname"] for p in result["participants"]}
    assert nicknames == {"Alice", "Bob"}


def test_get_room_state_participant_is_host_flag() -> None:
    room = _make_room()
    participants = [_make_participant("Alice", is_host=True)]
    session = _make_session(room, participants)
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["participants"][0]["is_host"] is True


def test_get_room_state_current_song_none_when_waiting() -> None:
    room = _make_room(RoomStatus.WAITING.value)
    session = _make_session(room, participants=[])
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["current_song"] is None


def test_get_room_state_current_song_none_when_no_playing_song() -> None:
    room = _make_room(RoomStatus.ROUND_IN_PROGRESS.value)
    round_ = _make_round(room.id)
    session = _make_session(
        room, participants=[], round_=round_, current_song=None, total_songs=10
    )
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["current_song"] is None


def test_get_room_state_returns_current_song_when_round_in_progress() -> None:
    room = _make_room(RoomStatus.ROUND_IN_PROGRESS.value)
    round_ = _make_round(room.id)
    song = _make_song(round_.id, index=2)
    session = _make_session(
        room, participants=[], round_=round_, current_song=song, total_songs=10
    )
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["current_song"] is not None
    cs = result["current_song"]
    assert cs["song_id"] == song.id
    assert cs["song_index"] == 2
    assert cs["round_id"] == round_.id
    assert cs["total_songs"] == 10


def test_get_room_state_current_song_ends_at_is_iso_string() -> None:
    room = _make_room(RoomStatus.ROUND_IN_PROGRESS.value)
    round_ = _make_round(room.id)
    song = _make_song(round_.id)
    session = _make_session(
        room, participants=[], round_=round_, current_song=song, total_songs=5
    )
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    ends_at = result["current_song"]["ends_at"]  # type: ignore[index]
    assert isinstance(ends_at, str)
    assert "T" in ends_at


def test_get_room_state_current_song_none_when_no_active_round() -> None:
    room = _make_room(RoomStatus.ROUND_IN_PROGRESS.value)
    session = _make_session(room, participants=[], round_=None, total_songs=0)
    service = RoomService(session)
    result = service.get_room_state("ABC123")
    assert result["current_song"] is None
