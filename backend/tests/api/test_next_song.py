"""TDD — T-034: API enchaîner les chansons, fin de manche."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import RoundNotInProgressError
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_HOST_ID = uuid4()
_SONG_ID = uuid4()
_ROOM_ID = uuid4()
_ROUND_ID = uuid4()


def _make_reveal_result(
    *,
    round_finished: bool = False,
    round_leaderboard: list[dict] | None = None,
) -> dict:
    return {
        "song_id": _SONG_ID,
        "room_id": _ROOM_ID,
        "title": "One More Time",
        "artist": "Daft Punk",
        "player_results": [],
        "mini_leaderboard": [],
        "round_finished": round_finished,
        "round_leaderboard": round_leaderboard or [],
    }


class _FakeService:
    def __init__(
        self,
        reveal_result: dict | None = None,
        reveal_exc: Exception | None = None,
        start_song_exc: Exception | None = None,
    ) -> None:
        self._reveal_result = reveal_result
        self._reveal_exc = reveal_exc
        self._start_song_exc = start_song_exc

    def create_room(self, *a: object, **kw: object) -> dict:
        return {}

    def join_room(self, *a: object, **kw: object) -> dict:
        return {}

    def start_round(self, *a: object, **kw: object) -> dict:
        return {}

    def start_song(self, round_id: UUID, song_index: int) -> dict:
        if self._start_song_exc is not None:
            raise self._start_song_exc
        from datetime import datetime, timedelta, timezone

        now = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
        return {
            "song_id": uuid4(),
            "round_id": round_id,
            "room_id": _ROOM_ID,
            "song_index": song_index,
            "started_at": now,
            "ends_at": now + timedelta(seconds=30),
        }

    def lock_song(self, *a: object, **kw: object) -> dict:
        return {}

    def submit_answer(self, *a: object, **kw: object) -> dict:
        return {}

    def get_song_summary(self, *a: object, **kw: object) -> dict:
        return {}

    def override_answer(self, *a: object, **kw: object) -> dict:
        return {}

    def reveal_song(self, song_id: UUID, host_id: UUID) -> dict:
        if self._reveal_exc is not None:
            raise self._reveal_exc
        assert self._reveal_result is not None
        return self._reveal_result


@pytest.fixture
def mock_manager() -> MagicMock:
    m = MagicMock(spec=RoomConnectionManager)
    m.broadcast_to_room = AsyncMock()
    return m


# ── 1. champs round_finished et round_leaderboard dans la réponse ─────────────


def test_reveal_non_last_song_response_includes_round_finished_false(
    mock_manager: MagicMock,
) -> None:
    fake = _FakeService(reveal_result=_make_reveal_result(round_finished=False))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        client = TestClient(app)
        data = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_id": str(_HOST_ID)}
        ).json()
        assert data["round_finished"] is False
        assert data["round_leaderboard"] == []
    finally:
        app.dependency_overrides.clear()


def test_reveal_last_song_response_includes_round_finished_true(
    mock_manager: MagicMock,
) -> None:
    alice_id = uuid4()
    lb = [
        {
            "rank": 1,
            "participant_id": str(alice_id),
            "nickname": "Alice",
            "round_points": 200,
        }
    ]
    fake = _FakeService(
        reveal_result=_make_reveal_result(round_finished=True, round_leaderboard=lb)
    )
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        client = TestClient(app)
        data = client.post(
            f"/songs/{_SONG_ID}/reveal", json={"host_id": str(_HOST_ID)}
        ).json()
        assert data["round_finished"] is True
        assert len(data["round_leaderboard"]) == 1
        assert UUID(data["round_leaderboard"][0]["participant_id"]) == alice_id
        assert data["round_leaderboard"][0]["round_points"] == 200
    finally:
        app.dependency_overrides.clear()


# ── 2. broadcast round.finished sur la dernière chanson ───────────────────────


def test_reveal_last_song_broadcasts_round_finished_event(
    mock_manager: MagicMock,
) -> None:
    fake = _FakeService(reveal_result=_make_reveal_result(round_finished=True))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        client = TestClient(app)
        client.post(f"/songs/{_SONG_ID}/reveal", json={"host_id": str(_HOST_ID)})
        calls = mock_manager.broadcast_to_room.call_args_list
        events = [c.args[1]["event"] for c in calls]
        assert "round.finished" in events
        finished_call = next(c for c in calls if c.args[1]["event"] == "round.finished")
        payload = finished_call.args[1]
        assert payload["data"]["room_id"] == str(_ROOM_ID)
    finally:
        app.dependency_overrides.clear()


def test_reveal_non_last_song_does_not_broadcast_round_finished(
    mock_manager: MagicMock,
) -> None:
    fake = _FakeService(reveal_result=_make_reveal_result(round_finished=False))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        client = TestClient(app)
        client.post(f"/songs/{_SONG_ID}/reveal", json={"host_id": str(_HOST_ID)})
        calls = mock_manager.broadcast_to_room.call_args_list
        events = [c.args[1]["event"] for c in calls]
        assert "round.finished" not in events
    finally:
        app.dependency_overrides.clear()


# ── 4. refus chanson 11 (round terminé) ───────────────────────────────────────


def test_start_song_after_round_finished_returns_409(
    mock_manager: MagicMock,
) -> None:
    """Démarrer une chanson sur un round terminé retourne 409."""
    from src.api.deps import get_db_factory, get_session

    fake = _FakeService(start_song_exc=RoundNotInProgressError("Round is finished"))
    app.dependency_overrides[get_room_service] = lambda: fake
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    try:
        client = TestClient(app)
        response = client.post(f"/rounds/{_ROUND_ID}/songs/10/start")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
