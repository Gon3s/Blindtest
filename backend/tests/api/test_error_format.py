"""T-057 — Format d'erreur unifié : code + message lisible utilisateur."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.api.routes.songs import get_room_service as get_song_service
from src.domain.exceptions import (
    NicknameAlreadyTakenError,
    NotHostError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
    SongNotAcceptingAnswersError,
    SongNotFoundError,
    SongNotLockedError,
    SongNotRevealableError,
)
from src.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_error_structure(data: dict) -> None:
    """Vérifie que la réponse contient code et message (format unifié)."""
    assert "code" in data, f"Clé 'code' absente : {data}"
    assert "message" in data, f"Clé 'message' absente : {data}"
    assert isinstance(data["code"], str) and data["code"]
    assert isinstance(data["message"], str) and data["message"]


def _assert_no_stacktrace(data: dict) -> None:
    """Le message ne doit pas contenir de termes techniques."""
    message = data.get("message", "")
    technical_terms = ["Error", "Exception", "Traceback", "traceback", "ValueError"]
    for term in technical_terms:
        msg_label = f"Terme technique '{term}' dans message : {message!r}"
        assert term not in message, msg_label


# ---------------------------------------------------------------------------
# Service fakes
# ---------------------------------------------------------------------------

class _RaisingService:
    """Service qui lève une exception configurable."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def __getattr__(self, _name: str):  # type: ignore[override]
        def _raise(*_a, **_kw):  # type: ignore[misc]
            raise self._exc
        return _raise


def _client_raising(exc: Exception) -> TestClient:
    fake = _RaisingService(exc)
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_song_service] = lambda: fake
    client = TestClient(app, raise_server_exceptions=False)
    return client


# ---------------------------------------------------------------------------
# Tests — codes d'erreur connus
# ---------------------------------------------------------------------------

class TestRoomErrors:
    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_room_not_found_returns_404_with_code(self):
        client = _client_raising(RoomNotFoundError("not found"))
        resp = client.post("/rooms/BADCODE/join", json={"nickname": "Bob"})
        assert resp.status_code == 404
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "room_not_found"
        _assert_no_stacktrace(data)

    def test_room_not_found_message_is_user_friendly(self):
        client = _client_raising(RoomNotFoundError())
        resp = client.post("/rooms/BADCODE/join", json={"nickname": "Bob"})
        data = resp.json()
        assert data["message"] == "Code de salle invalide. Vérifie le code et réessaie."
        _assert_no_stacktrace(data)

    def test_nickname_taken_returns_409_with_code(self):
        client = _client_raising(NicknameAlreadyTakenError())
        resp = client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "nickname_taken"
        _assert_no_stacktrace(data)

    def test_room_not_joinable_returns_409_with_code(self):
        client = _client_raising(RoomNotJoinableError())
        resp = client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "room_already_started"
        _assert_no_stacktrace(data)

    def test_not_waiting_returns_409_with_code(self):
        client = _client_raising(RoomNotWaitingError())
        resp = client.get("/rooms/ABC123")
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "room_not_waiting"
        _assert_no_stacktrace(data)

    def test_not_host_returns_403_with_code(self):
        client = _client_raising(NotHostError())
        resp = client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        assert resp.status_code == 403
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "not_host"
        _assert_no_stacktrace(data)


class TestSongErrors:
    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_answer_too_late_returns_409_with_code(self):
        client = _client_raising(SongNotAcceptingAnswersError())
        song_id = uuid4()
        participant_id = uuid4()
        resp = client.post(
            f"/songs/{song_id}/answers",
            json={"participant_id": str(participant_id), "text": "Test"},
        )
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "answer_too_late"
        _assert_no_stacktrace(data)

    def test_song_not_found_returns_404_with_code(self):
        client = _client_raising(SongNotFoundError())
        song_id = uuid4()
        participant_id = uuid4()
        resp = client.post(
            f"/songs/{song_id}/answers",
            json={"participant_id": str(participant_id), "text": "Test"},
        )
        assert resp.status_code == 404
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "song_not_found"
        _assert_no_stacktrace(data)

    def test_song_not_locked_returns_409_with_code(self):
        client = _client_raising(SongNotLockedError())
        song_id = uuid4()
        resp = client.post(
            f"/songs/{song_id}/summary",
            json={"host_token": "tok"},
        )
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "song_not_locked"
        _assert_no_stacktrace(data)

    def test_song_not_revealable_returns_409_with_code(self):
        client = _client_raising(SongNotRevealableError())
        song_id = uuid4()
        resp = client.post(
            f"/songs/{song_id}/reveal",
            json={"host_token": "tok"},
        )
        assert resp.status_code == 409
        data = resp.json()
        _assert_error_structure(data)
        assert data["code"] == "song_not_revealable"
        _assert_no_stacktrace(data)


class TestErrorMessageQuality:
    """Les messages doivent être compréhensibles par un non-technicien."""

    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    @pytest.mark.parametrize("exc,route,method,payload", [
        (RoomNotFoundError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
        (NicknameAlreadyTakenError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
        (RoomNotJoinableError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
    ])
    def test_message_does_not_contain_exception_class_name(
        self, exc, route, method, payload
    ):
        client = _client_raising(exc)
        resp = getattr(client, method)(route, json=payload)
        data = resp.json()
        if "message" in data:
            assert type(exc).__name__ not in data["message"]

    @pytest.mark.parametrize("exc,route,method,payload", [
        (RoomNotFoundError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
        (NicknameAlreadyTakenError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
        (RoomNotJoinableError(), "/rooms/X/join", "post", {"nickname": "Bob"}),
    ])
    def test_message_is_non_empty_string(self, exc, route, method, payload):
        client = _client_raising(exc)
        resp = getattr(client, method)(route, json=payload)
        data = resp.json()
        assert isinstance(data.get("message"), str)
        assert len(data["message"]) > 5
