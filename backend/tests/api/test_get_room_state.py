from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import RoomNotFoundError
from src.main import app


class _FakeService:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def get_room_state(self, code: str):
        if self._exc:
            raise self._exc
        return self._result


def _client(result=None, exc=None) -> TestClient:
    app.dependency_overrides[get_room_service] = lambda: _FakeService(result, exc)
    return TestClient(app)


def _room_result(status="waiting", current_song=None):
    return {
        "room_id": uuid4(),
        "code": "ABC123",
        "status": status,
        "participants": [
            {"participant_id": uuid4(), "nickname": "Alice", "is_host": True},
        ],
        "current_song": current_song,
    }


def test_get_room_state_returns_200():
    client = _client(_room_result())
    try:
        response = client.get("/rooms/ABC123")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_get_room_state_returns_room_id_code_status():
    result = _room_result()
    client = _client(result)
    try:
        data = client.get("/rooms/ABC123").json()
        assert UUID(data["room_id"]) == result["room_id"]
        assert data["code"] == "ABC123"
        assert data["status"] == "waiting"
    finally:
        app.dependency_overrides.clear()


def test_get_room_state_includes_participants():
    client = _client(_room_result())
    try:
        data = client.get("/rooms/ABC123").json()
        assert len(data["participants"]) == 1
        assert data["participants"][0]["nickname"] == "Alice"
        assert data["participants"][0]["is_host"] is True
    finally:
        app.dependency_overrides.clear()


def test_get_room_state_current_song_none_when_waiting():
    client = _client(_room_result(status="waiting", current_song=None))
    try:
        data = client.get("/rooms/ABC123").json()
        assert data["current_song"] is None
    finally:
        app.dependency_overrides.clear()


def test_get_room_state_includes_current_song_when_round_in_progress():
    song_id = uuid4()
    round_id = uuid4()
    current_song = {
        "song_id": song_id,
        "song_index": 2,
        "round_id": round_id,
        "ends_at": "2026-05-20T20:00:00+00:00",
        "preview_url": "https://example.com/preview.mp3",
        "total_songs": 10,
    }
    result = _room_result(status="round_in_progress", current_song=current_song)
    client = _client(result)
    try:
        data = client.get("/rooms/ABC123").json()
        assert data["status"] == "round_in_progress"
        assert data["current_song"]["song_index"] == 2
        assert data["current_song"]["total_songs"] == 10
    finally:
        app.dependency_overrides.clear()


def test_get_room_state_returns_404_when_not_found():
    client = _client(exc=RoomNotFoundError("not found"))
    try:
        response = client.get("/rooms/XXXXXX")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
