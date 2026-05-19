"""TDD — POST /songs/{song_id}/reveal API (T-032)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import (
    NotHostError,
    SongNotFoundError,
    SongNotRevealableError,
)
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_HOST_TOKEN = "valid-host-token-for-reveal"
_SONG_ID = uuid4()
_ROOM_ID = uuid4()


def _make_reveal_result(
    *,
    player_results: list[dict] | None = None,
    mini_leaderboard: list[dict] | None = None,
) -> dict:
    return {
        "song_id": _SONG_ID,
        "room_id": _ROOM_ID,
        "title": "One More Time",
        "artist": "Daft Punk",
        "player_results": player_results or [],
        "mini_leaderboard": mini_leaderboard or [],
        "round_finished": False,
        "round_leaderboard": [],
    }


class _FakeRevealService:
    def __init__(
        self, result: dict | None = None, exc: Exception | None = None
    ) -> None:
        self._result = result
        self._exc = exc

    def create_room(self, *a: object, **kw: object) -> dict:
        return {}

    def join_room(self, *a: object, **kw: object) -> dict:
        return {}

    def start_round(self, *a: object, **kw: object) -> dict:
        return {}

    def start_song(self, *a: object, **kw: object) -> dict:
        return {}

    def lock_song(self, *a: object, **kw: object) -> dict:
        return {}

    def submit_answer(self, *a: object, **kw: object) -> dict:
        return {}

    def get_song_summary(self, *a: object, **kw: object) -> dict:
        return {}

    def override_answer(self, *a: object, **kw: object) -> dict:
        return {}

    def reveal_song(self, song_id: UUID, host_token: str) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result


@pytest.fixture
def reveal_result() -> dict:
    return _make_reveal_result()


@pytest.fixture
def reveal_client(reveal_result: dict) -> TestClient:
    fake = _FakeRevealService(result=reveal_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── 1. reveal OK ──────────────────────────────────────────────────────────────


def test_reveal_returns_200(reveal_client: TestClient) -> None:
    response = reveal_client.post(
        f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
    )
    assert response.status_code == 200


def test_reveal_returns_title_and_artist(reveal_client: TestClient) -> None:
    response = reveal_client.post(
        f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
    )
    data = response.json()
    assert data["title"] == "One More Time"
    assert data["artist"] == "Daft Punk"


def test_reveal_returns_song_id_and_room_id(reveal_client: TestClient) -> None:
    response = reveal_client.post(
        f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
    )
    data = response.json()
    assert UUID(data["song_id"]) == _SONG_ID
    assert UUID(data["room_id"]) == _ROOM_ID


def test_reveal_returns_player_results_list(reveal_client: TestClient) -> None:
    response = reveal_client.post(
        f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
    )
    data = response.json()
    assert "player_results" in data
    assert isinstance(data["player_results"], list)


def test_reveal_returns_mini_leaderboard_list(reveal_client: TestClient) -> None:
    response = reveal_client.post(
        f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
    )
    data = response.json()
    assert "mini_leaderboard" in data
    assert isinstance(data["mini_leaderboard"], list)


# ── player result structure ───────────────────────────────────────────────────


def test_reveal_player_result_fields() -> None:
    pid = uuid4()
    pr = {
        "participant_id": str(pid),
        "nickname": "Alice",
        "answer": "one more time",
        "title_found": True,
        "artist_found": False,
        "score": 117,
    }
    result = _make_reveal_result(player_results=[pr])
    fake = _FakeRevealService(result=result)
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
        )
        item = response.json()["player_results"][0]
        assert UUID(item["participant_id"]) == pid
        assert item["nickname"] == "Alice"
        assert item["answer"] == "one more time"
        assert item["title_found"] is True
        assert item["artist_found"] is False
        assert item["score"] == 117
    finally:
        app.dependency_overrides.clear()


# ── mini-leaderboard structure ────────────────────────────────────────────────


def test_reveal_mini_leaderboard_fields() -> None:
    pid = uuid4()
    lb = [
        {"rank": 1, "participant_id": str(pid), "nickname": "Bob", "total_points": 267}
    ]
    result = _make_reveal_result(mini_leaderboard=lb)
    fake = _FakeRevealService(result=result)
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
        )
        item = response.json()["mini_leaderboard"][0]
        assert item["rank"] == 1
        assert UUID(item["participant_id"]) == pid
        assert item["nickname"] == "Bob"
        assert item["total_points"] == 267
    finally:
        app.dependency_overrides.clear()


# ── 5. event song.revealed diffusé (vérifié via broadcast) ───────────────────


def test_reveal_broadcasts_song_revealed_event(reveal_result: dict) -> None:
    from unittest.mock import AsyncMock, MagicMock

    fake = _FakeRevealService(result=reveal_result)
    mock_manager = MagicMock(spec=RoomConnectionManager)
    mock_manager.broadcast_to_room = AsyncMock()

    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        client = TestClient(app)
        client.post(f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN})
        mock_manager.broadcast_to_room.assert_called_once()
        call_args = mock_manager.broadcast_to_room.call_args.args
        payload = call_args[1]
        assert payload["event"] == "song.revealed"
        assert str(_SONG_ID) == payload["data"]["song_id"]
        assert payload["data"]["title"] == "One More Time"
    finally:
        app.dependency_overrides.clear()


# ── erreurs ───────────────────────────────────────────────────────────────────


def test_reveal_song_not_found_returns_404() -> None:
    fake = _FakeRevealService(exc=SongNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            f"/songs/{uuid4()}/reveal", json={"host_token": _HOST_TOKEN}
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_reveal_not_revealable_returns_409() -> None:
    fake = _FakeRevealService(exc=SongNotRevealableError("still playing"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_token": _HOST_TOKEN}
        )
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_reveal_not_host_returns_403() -> None:
    fake = _FakeRevealService(exc=NotHostError("not the host"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_token": "wrong-token"}
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_reveal_missing_host_token_returns_422() -> None:
    fake = _FakeRevealService(result=_make_reveal_result())
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(f"/songs/{_SONG_ID}/reveal", json={})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
