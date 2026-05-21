from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import (
    ParticipantNotInRoomError,
    SongNotAcceptingAnswersError,
    SongNotFoundError,
)
from src.main import app

_FIXED_NOW = datetime(2026, 5, 16, 10, 0, 0, tzinfo=timezone.utc)
_VALID_BODY = {"participant_id": str(uuid4()), "text": "Daft Punk"}


def _make_submit_result() -> dict:
    return {
        "answer_id": uuid4(),
        "submitted_at": _FIXED_NOW,
        "validation_status": "not_found",
        "title_found": False,
        "artist_found": False,
    }


class _FakeAnswerService:
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
        return {}

    def lock_song(self, song_id: UUID) -> dict:
        return {}

    def submit_answer(self, song_id: UUID, participant_id: UUID, text: str) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result


@pytest.fixture
def submit_result() -> dict:
    return _make_submit_result()


@pytest.fixture
def answer_client(submit_result: dict) -> TestClient:
    fake = _FakeAnswerService(result=submit_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_submit_answer_ok_during_timer(answer_client: TestClient) -> None:
    response = answer_client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
    assert response.status_code == 201


def test_submit_answer_returns_answer_id(
    answer_client: TestClient, submit_result: dict
) -> None:
    response = answer_client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
    data = response.json()
    assert UUID(data["answer_id"]) == submit_result["answer_id"]


def test_submit_answer_empty_rejected(answer_client: TestClient) -> None:
    response = answer_client.post(
        f"/songs/{uuid4()}/answers",
        json={"participant_id": str(uuid4()), "text": ""},
    )
    assert response.status_code == 422


def test_submit_answer_after_timer_rejected() -> None:
    fake = _FakeAnswerService(exc=SongNotAcceptingAnswersError("song is locked"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_submit_answer_song_not_found_returns_404() -> None:
    fake = _FakeAnswerService(exc=SongNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_submit_answer_timestamp_is_server_time(
    answer_client: TestClient, submit_result: dict
) -> None:
    # Client sends no timestamp; submitted_at in response is the server-assigned value
    response = answer_client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
    data = response.json()
    parsed = datetime.fromisoformat(data["submitted_at"])
    assert parsed == submit_result["submitted_at"]


def test_submit_answer_validation_fields_present(
    answer_client: TestClient,
) -> None:
    response = answer_client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
    data = response.json()
    assert "title_found" in data
    assert "artist_found" in data
    assert "validation_status" in data


def test_submit_answer_wrong_participant_returns_403() -> None:
    fake = _FakeAnswerService(exc=ParticipantNotInRoomError("not in room"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_submit_answer_wrong_participant_returns_error_code() -> None:
    fake = _FakeAnswerService(exc=ParticipantNotInRoomError("not in room"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(f"/songs/{uuid4()}/answers", json=_VALID_BODY)
        assert response.json()["code"] == "participant_not_in_room"
    finally:
        app.dependency_overrides.clear()
