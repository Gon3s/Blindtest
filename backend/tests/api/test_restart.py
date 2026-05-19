from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_db_factory, get_session
from src.api.routes.rooms import get_music_provider, get_room_service
from src.domain.exceptions import RoomNotFinishedRoundError, RoomNotFoundError
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_FIXED_NOW = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
_RESTART_BODY = {"theme": "Rock 80s", "host_token": "test-host-token"}


class _FakeRestartService:
    def __init__(
        self, result: dict | None = None, exc: Exception | None = None
    ) -> None:
        self._result = result
        self._exc = exc

    def restart_round(
        self, room_id: UUID, host_token: str, theme: str, music_provider: object
    ) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result

    def start_song(self, round_id: UUID, song_index: int) -> dict:
        return {
            "song_id": uuid4(),
            "round_id": round_id,
            "room_id": uuid4(),
            "song_index": song_index,
            "started_at": _FIXED_NOW,
            "ends_at": _FIXED_NOW + timedelta(seconds=30),
            "preview_url": "https://example.com/preview.mp3",
        }


def _make_result(room_id: UUID | None = None) -> dict:
    return {
        "round_id": uuid4(),
        "room_id": room_id or uuid4(),
        "song_count": 10,
        "theme": "Rock 80s",
    }


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock(spec=RoomConnectionManager)
    manager.broadcast_to_room = AsyncMock()
    return manager


@pytest.fixture
def restart_result() -> dict:
    return _make_result()


@pytest.fixture
def restart_client(restart_result: dict, mock_manager: MagicMock) -> TestClient:
    fake = _FakeRestartService(result=restart_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_restart_returns_201(restart_client: TestClient) -> None:
    response = restart_client.post(
        f"/rooms/{uuid4()}/restart", json=_RESTART_BODY
    )
    assert response.status_code == 201


def test_restart_returns_round_id_and_song_count(
    restart_client: TestClient, restart_result: dict
) -> None:
    response = restart_client.post(
        f"/rooms/{uuid4()}/restart", json=_RESTART_BODY
    )
    data = response.json()
    assert UUID(data["round_id"]) == restart_result["round_id"]
    assert data["song_count"] == 10
    assert data["theme"] == "Rock 80s"


def test_restart_room_not_found_returns_404(mock_manager: MagicMock) -> None:
    fake = _FakeRestartService(exc=RoomNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rooms/{uuid4()}/restart", json=_RESTART_BODY)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_restart_room_not_finished_round_returns_409(mock_manager: MagicMock) -> None:
    fake = _FakeRestartService(exc=RoomNotFinishedRoundError("not finished"))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rooms/{uuid4()}/restart", json=_RESTART_BODY)
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_restart_broadcasts_round_started_event(
    restart_client: TestClient, restart_result: dict, mock_manager: MagicMock
) -> None:
    restart_client.post(f"/rooms/{uuid4()}/restart", json=_RESTART_BODY)
    events = [c.args[1]["event"] for c in mock_manager.broadcast_to_room.call_args_list]
    assert "round.started" in events


def test_restart_song_started_event_has_preview_url(
    restart_client: TestClient, mock_manager: MagicMock
) -> None:
    restart_client.post(f"/rooms/{uuid4()}/restart", json=_RESTART_BODY)
    calls = mock_manager.broadcast_to_room.call_args_list
    song_started = next(c for c in calls if c.args[1]["event"] == "song.started")
    data = song_started.args[1]["data"]
    assert "preview_url" in data
    assert data["preview_url"] == "https://example.com/preview.mp3"
