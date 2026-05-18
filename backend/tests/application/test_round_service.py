from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import RoomStatus
from src.domain.exceptions import RoomNotFoundError, RoomNotWaitingError
from src.domain.music_provider import TrackInfo
from src.infrastructure.models import RoomModel, RoundModel, SongModel


def _make_tracks(n: int = 10) -> list[TrackInfo]:
    return [TrackInfo(title=f"Song {i}", artist=f"Artist {i}") for i in range(n)]


class FakeMusicProvider:
    def __init__(self, tracks: list[TrackInfo] | None = None) -> None:
        self._tracks = tracks if tracks is not None else _make_tracks(10)

    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        return self._tracks[:limit]


def _make_room_mock(status: str = RoomStatus.WAITING.value) -> MagicMock:
    room = MagicMock(spec=RoomModel)
    room.id = uuid4()
    room.status = status
    room.config = {"max_songs_per_round": 10, "answer_duration_seconds": 30}
    return room


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def waiting_session(room_id: UUID) -> MagicMock:
    mock = MagicMock()
    room = _make_room_mock(status=RoomStatus.WAITING.value)
    room.id = room_id
    mock.query.return_value.filter_by.return_value.first.return_value = room
    mock.query.return_value.filter_by.return_value.count.return_value = 0
    return mock


@pytest.fixture
def service(waiting_session: MagicMock) -> RoomService:
    return RoomService(waiting_session)


def test_start_round_ok(service: RoomService, room_id: UUID) -> None:
    result = service.start_round(room_id, "Pop 90s", FakeMusicProvider())
    assert "round_id" in result
    assert isinstance(result["round_id"], UUID)
    assert result["room_id"] == room_id
    assert result["theme"] == "Pop 90s"


def test_start_round_10_songs_attached(
    service: RoomService, waiting_session: MagicMock, room_id: UUID
) -> None:
    service.start_round(room_id, "Pop 90s", FakeMusicProvider())
    added = [call.args[0] for call in waiting_session.add.call_args_list]
    songs = [m for m in added if isinstance(m, SongModel)]
    assert len(songs) == 10


def test_start_round_song_count_in_result(service: RoomService, room_id: UUID) -> None:
    result = service.start_round(room_id, "Pop 90s", FakeMusicProvider())
    assert result["song_count"] == 10


def test_start_round_round_model_persisted(
    service: RoomService, waiting_session: MagicMock, room_id: UUID
) -> None:
    service.start_round(room_id, "Pop 90s", FakeMusicProvider())
    added = [call.args[0] for call in waiting_session.add.call_args_list]
    rounds = [m for m in added if isinstance(m, RoundModel)]
    assert len(rounds) == 1
    assert rounds[0].theme == "Pop 90s"


def test_start_round_room_status_updated_to_round_in_progress(
    service: RoomService, waiting_session: MagicMock, room_id: UUID
) -> None:
    service.start_round(room_id, "Pop 90s", FakeMusicProvider())
    room = waiting_session.query.return_value.filter_by.return_value.first.return_value
    assert room.status == RoomStatus.ROUND_IN_PROGRESS.value


def test_start_round_room_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    service = RoomService(mock)
    with pytest.raises(RoomNotFoundError):
        service.start_round(uuid4(), "Pop 90s", FakeMusicProvider())


def test_start_round_room_not_waiting_raises() -> None:
    mock = MagicMock()
    room = _make_room_mock(status=RoomStatus.FINISHED.value)
    mock.query.return_value.filter_by.return_value.first.return_value = room
    service = RoomService(mock)
    with pytest.raises(RoomNotWaitingError):
        service.start_round(room.id, "Pop 90s", FakeMusicProvider())


def test_start_round_room_created_raises() -> None:
    # CREATED → ROUND_IN_PROGRESS invalid; open_room must happen first.
    mock = MagicMock()
    room = _make_room_mock(status=RoomStatus.CREATED.value)
    mock.query.return_value.filter_by.return_value.first.return_value = room
    service = RoomService(mock)
    with pytest.raises(RoomNotWaitingError):
        service.start_round(room.id, "Pop 90s", FakeMusicProvider())


# NOTE: No auth in MVP — host permission cannot be enforced at API level.
# Any caller who knows the room_id can start a round.
# Enforcement will be added when authentication is introduced (post-MVP).
def test_start_round_no_host_auth_limit_documented() -> None:
    """Placeholder: host-only guard is intentionally absent (no auth in MVP)."""
    assert True
