"""T-053 — Host token authorization tests (TDD)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_db_factory, get_session
from src.api.routes.rooms import get_music_provider, get_room_service
from src.domain.exceptions import InvalidHostTokenError
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_HOST_TOKEN = "valid-host-token-xyz123"
_FIXED_NOW = datetime(2026, 5, 19, 12, 0, 0, tzinfo=timezone.utc)


class _FakeHostService:
    def create_room(self, host_nickname: str) -> dict:
        return {
            "room_id": uuid4(),
            "code": "ABC123",
            "host_id": uuid4(),
            "host_token": _HOST_TOKEN,
        }

    def join_room(self, code: str, nickname: str) -> dict:
        return {"room_id": uuid4(), "participant_id": uuid4()}

    def start_round(
        self,
        room_id: UUID,
        host_token: str,
        theme: str,
        music_provider: object,
        answer_mode: object = None,
    ) -> dict:
        if host_token != _HOST_TOKEN:
            raise InvalidHostTokenError("invalid token")
        return {
            "round_id": uuid4(),
            "room_id": room_id,
            "song_count": 10,
            "theme": theme,
            "answer_mode": "both",
        }

    def start_song(self, round_id: UUID, song_index: int) -> dict:
        return {
            "song_id": uuid4(),
            "round_id": round_id,
            "room_id": uuid4(),
            "song_index": song_index,
            "started_at": _FIXED_NOW,
            "ends_at": _FIXED_NOW + timedelta(seconds=30),
            "preview_url": None,
        }

    def reveal_song(self, song_id: UUID, host_token: str) -> dict:
        if host_token != _HOST_TOKEN:
            raise InvalidHostTokenError("invalid token")
        return {
            "song_id": song_id,
            "room_id": uuid4(),
            "title": "Test Song",
            "artist": "Test Artist",
            "cover_url": None,
            "player_results": [],
            "mini_leaderboard": [],
            "round_finished": False,
            "round_leaderboard": [],
        }

    def get_song_summary(self, song_id: UUID, host_token: str) -> dict:
        if host_token != _HOST_TOKEN:
            raise InvalidHostTokenError("invalid token")
        return {
            "song_id": song_id,
            "title": "Test",
            "artist": "Artist",
            "total_answers": 0,
            "doubtful_count": 0,
            "answers": [],
        }

    def override_answer(
        self,
        song_id: UUID,
        answer_id: UUID,
        host_token: str,
        title_accepted: bool,
        artist_accepted: bool,
    ) -> dict:
        if host_token != _HOST_TOKEN:
            raise InvalidHostTokenError("invalid token")
        return {
            "answer_id": answer_id,
            "title_found": title_accepted,
            "artist_found": artist_accepted,
            "validation_status": "found",
            "score": 100,
        }

    def lock_song(self, song_id: UUID) -> dict:
        return {}

    def submit_answer(self, song_id: UUID, participant_id: UUID, text: str) -> dict:
        return {}

    def restart_round(
        self,
        room_id: UUID,
        host_token: str,
        theme: str,
        music_provider: object,
        answer_mode: object = None,
    ) -> dict:
        if host_token != _HOST_TOKEN:
            raise InvalidHostTokenError("invalid token")
        return {
            "round_id": uuid4(),
            "room_id": room_id,
            "song_count": 10,
            "theme": theme,
            "answer_mode": "both",
        }


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock(spec=RoomConnectionManager)
    manager.broadcast_to_room = AsyncMock()
    return manager


@pytest.fixture
def host_client(mock_manager: MagicMock) -> TestClient:
    fake = _FakeHostService()
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


# 1. Action host autorisée avec token valide → 201
def test_start_round_with_valid_host_token_returns_201(
    host_client: TestClient,
) -> None:
    response = host_client.post(
        f"/rooms/{uuid4()}/rounds",
        json={"theme": "Pop 90s", "host_token": _HOST_TOKEN},
    )
    assert response.status_code == 201


# 2. Action host refusée sans token → 422 (validation Pydantic)
def test_start_round_without_host_token_returns_422(host_client: TestClient) -> None:
    response = host_client.post(
        f"/rooms/{uuid4()}/rounds",
        json={"theme": "Pop 90s"},
    )
    assert response.status_code == 422


# 3. Action host refusée avec token invalide (participant joueur) → 403
def test_start_round_with_invalid_host_token_returns_403(
    host_client: TestClient,
) -> None:
    response = host_client.post(
        f"/rooms/{uuid4()}/rounds",
        json={"theme": "Pop 90s", "host_token": "wrong-token"},
    )
    assert response.status_code == 403


# 4. Restauration contexte host après refresh — même token marche à nouveau (stateless)
def test_host_token_remains_valid_across_multiple_requests(
    host_client: TestClient,
) -> None:
    room_id = uuid4()
    payload = {"theme": "Pop 90s", "host_token": _HOST_TOKEN}
    r1 = host_client.post(f"/rooms/{room_id}/rounds", json=payload)
    r2 = host_client.post(f"/rooms/{room_id}/rounds", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201


# host_token retourné à la création de salle
def test_create_room_returns_host_token(host_client: TestClient) -> None:
    response = host_client.post("/rooms", json={"host_nickname": "Alice"})
    assert response.status_code == 201
    data = response.json()
    assert "host_token" in data
    assert isinstance(data["host_token"], str)
    assert len(data["host_token"]) > 0


# reveal protégé par host_token
def test_reveal_with_valid_host_token_returns_200(host_client: TestClient) -> None:
    response = host_client.post(
        f"/songs/{uuid4()}/reveal",
        json={"host_token": _HOST_TOKEN},
    )
    assert response.status_code == 200


def test_reveal_with_invalid_host_token_returns_403(host_client: TestClient) -> None:
    response = host_client.post(
        f"/songs/{uuid4()}/reveal",
        json={"host_token": "wrong-token"},
    )
    assert response.status_code == 403


# summary protégé par host_token
def test_summary_with_valid_host_token_returns_200(host_client: TestClient) -> None:
    response = host_client.post(
        f"/songs/{uuid4()}/summary",
        json={"host_token": _HOST_TOKEN},
    )
    assert response.status_code == 200


def test_summary_with_invalid_host_token_returns_403(host_client: TestClient) -> None:
    response = host_client.post(
        f"/songs/{uuid4()}/summary",
        json={"host_token": "wrong-token"},
    )
    assert response.status_code == 403
