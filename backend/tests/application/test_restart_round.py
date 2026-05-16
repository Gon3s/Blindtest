from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import RoomStatus
from src.domain.exceptions import RoomNotFinishedRoundError, RoomNotFoundError
from src.domain.music_provider import TrackInfo
from src.infrastructure.models import RoundModel, SongModel


def _make_tracks(n: int = 10) -> list[TrackInfo]:
    return [TrackInfo(title=f"Song {i}", artist=f"Artist {i}") for i in range(n)]


class FakeMusicProvider:
    def __init__(self, tracks: list[TrackInfo] | None = None) -> None:
        self._tracks = tracks if tracks is not None else _make_tracks(10)

    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        return self._tracks[:limit]


def _make_room_mock(status: str = RoomStatus.ROUND_FINISHED.value) -> MagicMock:
    from src.infrastructure.models import RoomModel

    room = MagicMock(spec=RoomModel)
    room.id = uuid4()
    room.status = status
    return room


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def finished_session(room_id: UUID) -> MagicMock:
    mock = MagicMock()
    room = _make_room_mock(status=RoomStatus.ROUND_FINISHED.value)
    room.id = room_id
    mock.query.return_value.filter_by.return_value.first.return_value = room
    mock.query.return_value.filter_by.return_value.count.return_value = 1
    return mock


@pytest.fixture
def service(finished_session: MagicMock) -> RoomService:
    return RoomService(finished_session)


def test_restart_round_ok(service: RoomService, room_id: UUID) -> None:
    result = service.restart_round(room_id, "Rock 80s", FakeMusicProvider())
    assert "round_id" in result
    assert isinstance(result["round_id"], UUID)
    assert result["room_id"] == room_id
    assert result["theme"] == "Rock 80s"
    assert result["song_count"] == 10


def test_restart_round_group_preserved(
    service: RoomService, finished_session: MagicMock, room_id: UUID
) -> None:
    """No participant must be deleted on restart."""
    service.restart_round(room_id, "Rock 80s", FakeMusicProvider())
    assert not finished_session.delete.called


def test_restart_round_global_score_preserved(
    service: RoomService, finished_session: MagicMock, room_id: UUID
) -> None:
    """Score entries must not be wiped on restart."""
    service.restart_round(room_id, "Rock 80s", FakeMusicProvider())
    assert not finished_session.delete.called


def test_restart_round_uses_new_theme(
    service: RoomService, finished_session: MagicMock, room_id: UUID
) -> None:
    service.restart_round(room_id, "Jazz Classics", FakeMusicProvider())
    added = [call.args[0] for call in finished_session.add.call_args_list]
    rounds = [m for m in added if isinstance(m, RoundModel)]
    assert len(rounds) == 1
    assert rounds[0].theme == "Jazz Classics"


def test_restart_round_starts_at_song_index_zero(
    service: RoomService, finished_session: MagicMock, room_id: UUID
) -> None:
    """New round must have 10 songs starting at index 0."""
    service.restart_round(room_id, "Jazz Classics", FakeMusicProvider())
    added = [call.args[0] for call in finished_session.add.call_args_list]
    songs = [m for m in added if isinstance(m, SongModel)]
    assert len(songs) == 10
    assert min(s.index for s in songs) == 0


def test_restart_round_room_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    with pytest.raises(RoomNotFoundError):
        RoomService(mock).restart_round(uuid4(), "Rock 80s", FakeMusicProvider())


def test_restart_round_room_not_finished_raises() -> None:
    mock = MagicMock()
    room = _make_room_mock(status=RoomStatus.ROUND_IN_PROGRESS.value)
    mock.query.return_value.filter_by.return_value.first.return_value = room
    with pytest.raises(RoomNotFinishedRoundError):
        RoomService(mock).restart_round(room.id, "Rock 80s", FakeMusicProvider())
