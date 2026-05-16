"""TDD — GET /songs/{song_id}/summary API (T-029)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.enums import ValidationStatus
from src.domain.exceptions import NotHostError, SongNotFoundError, SongNotLockedError
from src.main import app

_HOST_ID = uuid4()
_SONG_ID = uuid4()


def _make_summary(
    *,
    title: str = "One More Time",
    artist: str = "Daft Punk",
    answers: list[dict] | None = None,
    doubtful_count: int = 0,
) -> dict:
    return {
        "song_id": _SONG_ID,
        "title": title,
        "artist": artist,
        "total_answers": len(answers or []),
        "doubtful_count": doubtful_count,
        "answers": answers or [],
    }


class _FakeSummaryService:
    def __init__(
        self, result: dict | None = None, exc: Exception | None = None
    ) -> None:
        self._result = result
        self._exc = exc

    # stubs for other methods
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

    def get_song_summary(self, song_id: UUID, host_id: UUID) -> dict:
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result


@pytest.fixture
def summary_result() -> dict:
    return _make_summary()


@pytest.fixture
def summary_client(summary_result: dict) -> TestClient:
    fake = _FakeSummaryService(result=summary_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── basic structure ───────────────────────────────────────────────────────────


def test_summary_returns_200(summary_client: TestClient) -> None:
    response = summary_client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
    assert response.status_code == 200


def test_summary_contains_title_and_artist(
    summary_client: TestClient, summary_result: dict
) -> None:
    response = summary_client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
    data = response.json()
    assert data["title"] == summary_result["title"]
    assert data["artist"] == summary_result["artist"]


def test_summary_contains_song_id(summary_client: TestClient) -> None:
    response = summary_client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
    data = response.json()
    assert UUID(data["song_id"]) == _SONG_ID


def test_summary_contains_total_answers_and_doubtful_count(
    summary_client: TestClient,
) -> None:
    response = summary_client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
    data = response.json()
    assert "total_answers" in data
    assert "doubtful_count" in data


# ── no doubtful answers ───────────────────────────────────────────────────────


def test_summary_no_doubtful_count_is_zero() -> None:
    result = _make_summary(doubtful_count=0, answers=[])
    fake = _FakeSummaryService(result=result)
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
        assert response.json()["doubtful_count"] == 0
    finally:
        app.dependency_overrides.clear()


# ── with doubtful answer ──────────────────────────────────────────────────────


def test_summary_with_doubtful_answer_count_is_one() -> None:
    doubtful_ans = {
        "answer_id": str(uuid4()),
        "participant_id": str(uuid4()),
        "nickname": "Alice",
        "text": "one more tyme",
        "validation_status": ValidationStatus.DOUBTFUL.value,
        "title_found": False,
        "artist_found": False,
    }
    result = _make_summary(doubtful_count=1, answers=[doubtful_ans])
    fake = _FakeSummaryService(result=result)
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
        data = response.json()
        assert data["doubtful_count"] == 1
        item_status = data["answers"][0]["validation_status"]
        assert item_status == ValidationStatus.DOUBTFUL.value
    finally:
        app.dependency_overrides.clear()


# ── raw answers visible ───────────────────────────────────────────────────────


def test_summary_answer_exposes_raw_text_and_nickname() -> None:
    ans = {
        "answer_id": str(uuid4()),
        "participant_id": str(uuid4()),
        "nickname": "Bob",
        "text": "daft punk",
        "validation_status": ValidationStatus.FOUND.value,
        "title_found": False,
        "artist_found": True,
    }
    result = _make_summary(answers=[ans])
    fake = _FakeSummaryService(result=result)
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
        item = response.json()["answers"][0]
        assert item["text"] == "daft punk"
        assert item["nickname"] == "Bob"
        assert item["artist_found"] is True
        assert item["title_found"] is False
    finally:
        app.dependency_overrides.clear()


# ── errors ────────────────────────────────────────────────────────────────────


def test_summary_song_not_found_returns_404() -> None:
    fake = _FakeSummaryService(exc=SongNotFoundError("not found"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{uuid4()}/summary?host_id={_HOST_ID}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_summary_song_not_locked_returns_409() -> None:
    fake = _FakeSummaryService(exc=SongNotLockedError("still playing"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary?host_id={_HOST_ID}")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_summary_wrong_host_returns_403() -> None:
    fake = _FakeSummaryService(exc=NotHostError("not the host"))
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary?host_id={uuid4()}")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_summary_missing_host_id_returns_422() -> None:
    fake = _FakeSummaryService(result=_make_summary())
    app.dependency_overrides[get_room_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get(f"/songs/{_SONG_ID}/summary")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
