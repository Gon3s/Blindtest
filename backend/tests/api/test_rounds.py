from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_db_factory, get_session
from src.api.routes.rooms import get_music_provider, get_room_service
from src.domain.exceptions import RoomNotFoundError, RoomNotWaitingError
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_FIXED_NOW = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)


class _FakeRoundService:
    def __init__(
        self, result: dict | None = None, exc: Exception | None = None
    ) -> None:
        self._result = result
        self._exc = exc

    def create_room(self, host_nickname: str) -> dict:
        return {}

    def join_room(self, code: str, nickname: str) -> dict:
        return {}

    def start_round(
        self,
        room_id: UUID,
        host_token: str,
        theme: str,
        music_provider: object,
        answer_mode: object = None,
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
    rid = room_id or uuid4()
    return {
        "round_id": uuid4(),
        "room_id": rid,
        "song_count": 10,
        "theme": "Pop 90s",
        "answer_mode": "both",
    }


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock(spec=RoomConnectionManager)
    manager.broadcast_to_room = AsyncMock()
    return manager


@pytest.fixture
def round_result() -> dict:
    return _make_result()


@pytest.fixture
def round_client(round_result: dict, mock_manager: MagicMock) -> TestClient:
    fake = _FakeRoundService(result=round_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


_ROUND_BODY = {"theme": "Pop 90s", "host_token": "test-host-token"}


def test_start_round_returns_201(round_client: TestClient) -> None:
    room_id = uuid4()
    response = round_client.post(f"/rooms/{room_id}/rounds", json=_ROUND_BODY)
    assert response.status_code == 201


def test_start_round_returns_round_id_and_song_count(
    round_client: TestClient, round_result: dict
) -> None:
    room_id = uuid4()
    response = round_client.post(f"/rooms/{room_id}/rounds", json=_ROUND_BODY)
    data = response.json()
    assert UUID(data["round_id"]) == round_result["round_id"]
    assert data["song_count"] == 10


def test_start_round_missing_theme_returns_422(round_client: TestClient) -> None:
    room_id = uuid4()
    response = round_client.post(f"/rooms/{room_id}/rounds", json={"host_token": "tok"})
    assert response.status_code == 422


def test_start_round_missing_host_token_returns_422(round_client: TestClient) -> None:
    room_id = uuid4()
    response = round_client.post(f"/rooms/{room_id}/rounds", json={"theme": "Pop 90s"})
    assert response.status_code == 422


def test_start_round_room_not_found_returns_404(mock_manager: MagicMock) -> None:
    fake = _FakeRoundService(exc=RoomNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rooms/{uuid4()}/rounds", json=_ROUND_BODY)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_start_round_room_not_waiting_returns_409(mock_manager: MagicMock) -> None:
    fake = _FakeRoundService(exc=RoomNotWaitingError("not waiting"))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rooms/{uuid4()}/rounds", json=_ROUND_BODY)
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_start_round_broadcasts_round_started_event(
    round_client: TestClient, round_result: dict, mock_manager: MagicMock
) -> None:
    room_id = uuid4()
    round_client.post(f"/rooms/{room_id}/rounds", json=_ROUND_BODY)
    calls = mock_manager.broadcast_to_room.call_args_list
    assert len(calls) >= 1
    _, broadcast_msg = calls[0].args
    assert broadcast_msg["event"] == "round.started"
    assert UUID(broadcast_msg["data"]["round_id"]) == round_result["round_id"]
    assert broadcast_msg["data"]["song_count"] == 10


def test_start_round_song_started_event_has_preview_url(
    round_client: TestClient, mock_manager: MagicMock
) -> None:
    round_client.post(f"/rooms/{uuid4()}/rounds", json=_ROUND_BODY)
    calls = mock_manager.broadcast_to_room.call_args_list
    song_started = next(c for c in calls if c.args[1]["event"] == "song.started")
    data = song_started.args[1]["data"]
    assert "preview_url" in data
    assert data["preview_url"] == "https://example.com/preview.mp3"
