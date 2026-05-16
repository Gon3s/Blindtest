from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import (
    AnswerNotFoundError,
    NotHostError,
    SongNotCorrectableError,
    SongNotFoundError,
)
from src.main import app

_HOST_ID = uuid4()
_VALID_BODY = {
    "host_id": str(_HOST_ID),
    "title_accepted": True,
    "artist_accepted": False,
}


def _make_override_result(
    title_found: bool = True,
    artist_found: bool = False,
    validation_status: str = "found",
    score: int = 117,
) -> dict:
    return {
        "answer_id": uuid4(),
        "title_found": title_found,
        "artist_found": artist_found,
        "validation_status": validation_status,
        "score": score,
    }


class _FakeOverrideService:
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
        return {}

    def get_song_summary(self, song_id: UUID, host_id: UUID) -> dict:
        return {}

    def override_answer(
        self,
        song_id: UUID,
        answer_id: UUID,
        host_id: UUID,
        title_accepted: bool,
        artist_accepted: bool,
    ) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result


@pytest.fixture
def override_result() -> dict:
    return _make_override_result()


@pytest.fixture
def override_client(override_result: dict) -> TestClient:
    fake = _FakeOverrideService(result=override_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_override_answer_ok_returns_200(override_client: TestClient) -> None:
    response = override_client.patch(
        f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
    )
    assert response.status_code == 200


def test_override_answer_returns_title_found(
    override_client: TestClient, override_result: dict
) -> None:
    response = override_client.patch(
        f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
    )
    data = response.json()
    assert data["title_found"] == override_result["title_found"]
    assert data["artist_found"] == override_result["artist_found"]


def test_override_answer_returns_score(
    override_client: TestClient, override_result: dict
) -> None:
    response = override_client.patch(
        f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
    )
    data = response.json()
    assert data["score"] == override_result["score"]


def test_override_answer_returns_validation_status(
    override_client: TestClient, override_result: dict
) -> None:
    response = override_client.patch(
        f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
    )
    data = response.json()
    assert data["validation_status"] == override_result["validation_status"]


def test_override_answer_not_host_returns_403() -> None:
    fake = _FakeOverrideService(exc=NotHostError("not host"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.patch(
            f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_override_answer_song_not_found_returns_404() -> None:
    fake = _FakeOverrideService(exc=SongNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.patch(
            f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_override_answer_not_found_returns_404() -> None:
    fake = _FakeOverrideService(exc=AnswerNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.patch(
            f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_override_answer_not_correctable_returns_409() -> None:
    fake = _FakeOverrideService(exc=SongNotCorrectableError("not correctable"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.patch(
            f"/songs/{uuid4()}/answers/{uuid4()}", json=_VALID_BODY
        )
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
