from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.routes.rooms import get_room_service
from src.api.routes.songs import get_db_factory, get_sleep
from src.domain.exceptions import (
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotFoundError,
    SongNotPlayableError,
)
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_FIXED_NOW = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
_ENDS_AT = _FIXED_NOW + timedelta(seconds=30)


def _make_start_result(
    round_id: UUID | None = None,
    room_id: UUID | None = None,
    preview_url: str | None = None,
) -> dict:
    return {
        "song_id": uuid4(),
        "round_id": round_id or uuid4(),
        "room_id": room_id or uuid4(),
        "song_index": 0,
        "started_at": _FIXED_NOW,
        "ends_at": _ENDS_AT,
        "preview_url": preview_url,
    }


class _FakeSongService:
    def __init__(
        self, result: dict | None = None, exc: Exception | None = None
    ) -> None:
        self._result = result
        self._exc = exc

    def create_room(self, host_nickname: str) -> dict:
        return {}

    def join_room(self, code: str, nickname: str) -> dict:
        return {}

    def start_round(self, room_id: UUID, theme: str, music_provider: object) -> dict:
        return {}

    def start_song(self, round_id: UUID, song_index: int) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result

    def lock_song(self, song_id: UUID) -> dict:
        return {}


async def _instant_sleep(delay: float) -> None:
    pass


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock(spec=RoomConnectionManager)
    manager.broadcast_to_room = AsyncMock()
    return manager


@pytest.fixture
def start_result() -> dict:
    return _make_start_result()


@pytest.fixture
def song_client(start_result: dict, mock_manager: MagicMock) -> TestClient:
    fake = _FakeSongService(result=start_result)
    mock_factory = MagicMock()
    mock_factory.return_value = MagicMock()

    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_start_song_returns_200(song_client: TestClient, start_result: dict) -> None:
    round_id = start_result["round_id"]
    response = song_client.post(f"/rounds/{round_id}/songs/0/start")
    assert response.status_code == 200


def test_start_song_returns_song_id(
    song_client: TestClient, start_result: dict
) -> None:
    round_id = start_result["round_id"]
    response = song_client.post(f"/rounds/{round_id}/songs/0/start")
    data = response.json()
    assert UUID(data["song_id"]) == start_result["song_id"]


def test_start_song_returns_started_at_and_ends_at(
    song_client: TestClient, start_result: dict
) -> None:
    round_id = start_result["round_id"]
    response = song_client.post(f"/rounds/{round_id}/songs/0/start")
    data = response.json()
    assert data["started_at"] is not None
    assert data["ends_at"] is not None


def test_start_song_broadcasts_song_started(
    song_client: TestClient, start_result: dict, mock_manager: MagicMock
) -> None:
    round_id = start_result["round_id"]
    song_client.post(f"/rounds/{round_id}/songs/0/start")
    mock_manager.broadcast_to_room.assert_called()
    call_args = mock_manager.broadcast_to_room.call_args_list[0].args
    msg = call_args[1]
    assert msg["event"] == "song.started"


def test_start_song_started_event_has_correct_data(
    song_client: TestClient, start_result: dict, mock_manager: MagicMock
) -> None:
    round_id = start_result["round_id"]
    song_client.post(f"/rounds/{round_id}/songs/0/start")
    call_args = mock_manager.broadcast_to_room.call_args_list[0].args
    data = call_args[1]["data"]
    assert UUID(data["song_id"]) == start_result["song_id"]
    assert data["song_index"] == 0
    assert "started_at" in data
    assert "ends_at" in data


def test_start_song_round_not_found_returns_404(mock_manager: MagicMock) -> None:
    fake = _FakeSongService(exc=RoundNotFoundError("not found"))
    mock_factory = MagicMock()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rounds/{uuid4()}/songs/0/start")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_start_song_round_not_in_progress_returns_409(mock_manager: MagicMock) -> None:
    fake = _FakeSongService(exc=RoundNotInProgressError("not in progress"))
    mock_factory = MagicMock()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rounds/{uuid4()}/songs/0/start")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_start_song_song_not_found_returns_404(mock_manager: MagicMock) -> None:
    fake = _FakeSongService(exc=SongNotFoundError("not found"))
    mock_factory = MagicMock()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rounds/{uuid4()}/songs/0/start")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_start_song_song_not_playable_returns_409(mock_manager: MagicMock) -> None:
    fake = _FakeSongService(exc=SongNotPlayableError("not playable"))
    mock_factory = MagicMock()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rounds/{uuid4()}/songs/0/start")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def _make_song_client(result: dict, manager: MagicMock) -> TestClient:
    fake = _FakeSongService(result=result)
    mock_factory = MagicMock()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: manager
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    app.dependency_overrides[get_db_factory] = lambda: mock_factory
    app.dependency_overrides[get_session] = lambda: MagicMock()
    return TestClient(app)


def test_start_song_started_event_has_preview_url_when_available(
    mock_manager: MagicMock,
) -> None:
    result = _make_start_result(preview_url="https://example.com/preview.mp3")
    client = _make_song_client(result, mock_manager)
    try:
        client.post(f"/rounds/{result['round_id']}/songs/0/start")
        data = mock_manager.broadcast_to_room.call_args_list[0].args[1]["data"]
        assert data["preview_url"] == "https://example.com/preview.mp3"
    finally:
        app.dependency_overrides.clear()


def test_start_song_started_event_has_preview_url_null_when_unavailable(
    mock_manager: MagicMock,
) -> None:
    result = _make_start_result(preview_url=None)
    client = _make_song_client(result, mock_manager)
    try:
        client.post(f"/rounds/{result['round_id']}/songs/0/start")
        data = mock_manager.broadcast_to_room.call_args_list[0].args[1]["data"]
        assert data["preview_url"] is None
    finally:
        app.dependency_overrides.clear()
