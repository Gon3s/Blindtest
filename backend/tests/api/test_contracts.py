"""Contract tests — payload shapes for API responses and WebSocket events.

These tests freeze the contract between backend, frontend and WS clients.
They do NOT test business logic — only that the right keys/types are present.
"""

import asyncio
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.deps import auto_lock_song, get_db_factory, get_session, get_sleep
from src.api.routes.rooms import get_music_provider, get_room_service
from src.infrastructure.db import get_db
from src.infrastructure.ws_manager import RoomConnectionManager, get_ws_manager
from src.main import app

_FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_ENDS_AT = _FIXED_NOW + timedelta(seconds=30)


# ── shared fakes ──────────────────────────────────────────────────────────────


class _FakeSession:
    def __init__(self, participants: list[object] | None = None) -> None:
        self._participants = participants or []

    def query(self, model: type) -> "_FakeSession":
        return self

    def filter_by(self, **kwargs: object) -> "_FakeSession":
        return self

    def all(self) -> list[object]:
        return self._participants

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


class _FakeParticipant:
    def __init__(self, pid: UUID, nickname: str, is_host: bool) -> None:
        self.id = pid
        self.nickname = nickname
        self.is_host = is_host


class _BaseService:
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

    def reveal_song(self, *a: object, **kw: object) -> dict:
        return {}

    def restart_round(self, *a: object, **kw: object) -> dict:
        return {}


async def _instant_sleep(delay: float) -> None:
    pass


def _empty_db() -> Generator[_FakeSession, None, None]:
    yield _FakeSession()


@pytest.fixture
def mock_manager() -> MagicMock:
    m = MagicMock(spec=RoomConnectionManager)
    m.broadcast_to_room = AsyncMock()
    return m


# ── 1. POST /rooms ─────────────────────────────────────────────────────────────


def test_create_room_response_all_keys() -> None:
    room_id, host_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def create_room(self, host_nickname: str) -> dict:
            return {"room_id": room_id, "code": "ABC123", "host_id": host_id}

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    try:
        data = TestClient(app).post("/rooms", json={"host_nickname": "Alice"}).json()
        assert {"room_id", "code", "host_id"} == set(data.keys())
        assert UUID(data["room_id"]) == room_id
        assert isinstance(data["code"], str)
        assert UUID(data["host_id"]) == host_id
    finally:
        app.dependency_overrides.clear()


# ── 2. POST /rooms/{code}/join ─────────────────────────────────────────────────


def test_join_room_response_all_keys() -> None:
    room_id, participant_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def join_room(self, code: str, nickname: str) -> dict:
            return {"room_id": room_id, "participant_id": participant_id}

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    try:
        data = TestClient(app).post(
            "/rooms/ABC123/join", json={"nickname": "Bob"}
        ).json()
        assert {"room_id", "participant_id"} == set(data.keys())
        assert UUID(data["room_id"]) == room_id
        assert UUID(data["participant_id"]) == participant_id
    finally:
        app.dependency_overrides.clear()


# ── 3. POST /songs/{id}/answers — answer feedback ─────────────────────────────


def test_submit_answer_response_all_keys() -> None:
    answer_id = uuid4()

    class _Svc(_BaseService):
        def submit_answer(self, song_id: UUID, participant_id: UUID, text: str) -> dict:
            return {
                "answer_id": answer_id,
                "submitted_at": _FIXED_NOW,
                "validation_status": "found",
                "title_found": True,
                "artist_found": False,
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    try:
        data = TestClient(app).post(
            f"/songs/{uuid4()}/answers",
            json={"participant_id": str(uuid4()), "text": "Daft Punk"},
        ).json()
        expected = {
            "answer_id", "submitted_at", "validation_status",
            "title_found", "artist_found",
        }
        assert expected == set(data.keys())
        assert UUID(data["answer_id"]) == answer_id
        assert data["validation_status"] in ("not_found", "found", "doubtful")
        assert isinstance(data["title_found"], bool)
        assert isinstance(data["artist_found"], bool)
        datetime.fromisoformat(data["submitted_at"])
    finally:
        app.dependency_overrides.clear()


# ── 4. POST /songs/{id}/reveal — full response shape ──────────────────────────


def test_reveal_response_top_level_keys(mock_manager: MagicMock) -> None:
    song_id, room_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": song_id,
                "room_id": room_id,
                "title": "One More Time",
                "artist": "Daft Punk",
                "player_results": [],
                "mini_leaderboard": [],
                "round_finished": False,
                "round_leaderboard": [],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        data = TestClient(app).post(
            f"/songs/{song_id}/reveal", json={"host_id": str(uuid4())}
        ).json()
        required = {
            "song_id",
            "room_id",
            "title",
            "artist",
            "player_results",
            "mini_leaderboard",
            "round_finished",
            "round_leaderboard",
        }
        assert required == set(data.keys())
        assert isinstance(data["round_finished"], bool)
        assert isinstance(data["player_results"], list)
        assert isinstance(data["mini_leaderboard"], list)
        assert isinstance(data["round_leaderboard"], list)
    finally:
        app.dependency_overrides.clear()


def test_reveal_player_result_item_shape(mock_manager: MagicMock) -> None:
    pid = uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": uuid4(),
                "room_id": uuid4(),
                "title": "Get Lucky",
                "artist": "Daft Punk",
                "player_results": [
                    {
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "answer": "get lucky",
                        "title_found": True,
                        "artist_found": True,
                        "score": 200,
                    }
                ],
                "mini_leaderboard": [],
                "round_finished": False,
                "round_leaderboard": [],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        data = TestClient(app).post(
            f"/songs/{uuid4()}/reveal", json={"host_id": str(uuid4())}
        ).json()
        item = data["player_results"][0]
        pr_keys = {
            "participant_id", "nickname", "answer",
            "title_found", "artist_found", "score",
        }
        assert pr_keys == set(item.keys())
        assert UUID(item["participant_id"]) == pid
        assert isinstance(item["title_found"], bool)
        assert isinstance(item["artist_found"], bool)
        assert isinstance(item["score"], int)
    finally:
        app.dependency_overrides.clear()


def test_reveal_mini_leaderboard_item_shape(mock_manager: MagicMock) -> None:
    pid = uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": uuid4(),
                "room_id": uuid4(),
                "title": "Get Lucky",
                "artist": "Daft Punk",
                "player_results": [],
                "mini_leaderboard": [
                    {
                        "rank": 1,
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "total_points": 200,
                    }
                ],
                "round_finished": False,
                "round_leaderboard": [],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        data = TestClient(app).post(
            f"/songs/{uuid4()}/reveal", json={"host_id": str(uuid4())}
        ).json()
        item = data["mini_leaderboard"][0]
        lb_keys = {"rank", "participant_id", "nickname", "total_points"}
        assert lb_keys == set(item.keys())
        assert item["rank"] == 1
        assert UUID(item["participant_id"]) == pid
        assert isinstance(item["total_points"], int)
    finally:
        app.dependency_overrides.clear()


def test_reveal_round_leaderboard_item_shape(mock_manager: MagicMock) -> None:
    pid = uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": uuid4(),
                "room_id": uuid4(),
                "title": "Get Lucky",
                "artist": "Daft Punk",
                "player_results": [],
                "mini_leaderboard": [],
                "round_finished": True,
                "round_leaderboard": [
                    {
                        "rank": 1,
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "round_points": 200,
                    }
                ],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        data = TestClient(app).post(
            f"/songs/{uuid4()}/reveal", json={"host_id": str(uuid4())}
        ).json()
        assert data["round_finished"] is True
        item = data["round_leaderboard"][0]
        rl_keys = {"rank", "participant_id", "nickname", "round_points"}
        assert rl_keys == set(item.keys())
        assert item["rank"] == 1
        assert UUID(item["participant_id"]) == pid
        assert isinstance(item["round_points"], int)
    finally:
        app.dependency_overrides.clear()


# ── 5. WS room.state — participant item shape ──────────────────────────────────


def test_room_state_participant_shape() -> None:
    pid = uuid4()
    participant = _FakeParticipant(pid, "Alice", True)

    def _db_with_participant() -> Generator[_FakeSession, None, None]:
        yield _FakeSession([participant])

    app.dependency_overrides[get_db] = _db_with_participant
    try:
        with TestClient(app).websocket_connect(f"/ws/rooms/{uuid4()}") as ws:
            data = ws.receive_json()
        assert data["event"] == "room.state"
        assert {"room_id", "participants"} == set(data["data"].keys())
        p = data["data"]["participants"][0]
        assert {"participant_id", "nickname", "is_host"} == set(p.keys())
        assert UUID(p["participant_id"]) == pid
        assert p["nickname"] == "Alice"
        assert p["is_host"] is True
    finally:
        app.dependency_overrides.clear()


# ── 6. WS participant.joined — event shape ─────────────────────────────────────


def test_participant_joined_event_shape() -> None:
    room_id, participant_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def join_room(self, code: str, nickname: str) -> dict:
            return {"room_id": room_id, "participant_id": participant_id}

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_db] = _empty_db
    try:
        client = TestClient(app)
        with client.websocket_connect(f"/ws/rooms/{room_id}") as ws:
            ws.receive_json()  # consume room.state
            client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
            data = ws.receive_json()
        assert data["event"] == "participant.joined"
        d = data["data"]
        assert {"participant_id", "nickname", "is_host"} == set(d.keys())
        assert UUID(d["participant_id"]) == participant_id
        assert d["nickname"] == "Bob"
        assert isinstance(d["is_host"], bool)
    finally:
        app.dependency_overrides.clear()


# ── 7. WS song.started — event shape ──────────────────────────────────────────


def test_song_started_event_shape(mock_manager: MagicMock) -> None:
    song_id, round_id, room_id = uuid4(), uuid4(), uuid4()

    class _Svc(_BaseService):
        def start_song(self, round_id_: UUID, song_index: int) -> dict:
            return {
                "song_id": song_id,
                "round_id": round_id,
                "room_id": room_id,
                "song_index": 0,
                "started_at": _FIXED_NOW,
                "ends_at": _ENDS_AT,
                "preview_url": "https://cdn.deezer.com/preview.mp3",
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    try:
        TestClient(app).post(f"/rounds/{round_id}/songs/0/start")
        calls = mock_manager.broadcast_to_room.call_args_list
        call = next(c for c in calls if c.args[1]["event"] == "song.started")
        d = call.args[1]["data"]
        song_keys = {
            "song_id", "song_index", "round_id", "started_at", "ends_at", "preview_url"
        }
        assert song_keys == set(d.keys())
        assert UUID(d["song_id"]) == song_id
        assert UUID(d["round_id"]) == round_id
        assert isinstance(d["song_index"], int)
        assert isinstance(d["preview_url"], str)
        datetime.fromisoformat(d["started_at"])
        datetime.fromisoformat(d["ends_at"])
    finally:
        app.dependency_overrides.clear()


def test_song_started_preview_url_null_when_absent(mock_manager: MagicMock) -> None:
    round_id, room_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def start_song(self, round_id_: UUID, song_index: int) -> dict:
            return {
                "song_id": uuid4(),
                "round_id": round_id,
                "room_id": room_id,
                "song_index": 0,
                "started_at": _FIXED_NOW,
                "ends_at": _ENDS_AT,
                "preview_url": None,
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    try:
        TestClient(app).post(f"/rounds/{round_id}/songs/0/start")
        calls = mock_manager.broadcast_to_room.call_args_list
        call = next(c for c in calls if c.args[1]["event"] == "song.started")
        assert call.args[1]["data"]["preview_url"] is None
    finally:
        app.dependency_overrides.clear()


# ── 8. WS round.started — event shape (including theme) ───────────────────────


def test_round_started_event_shape(mock_manager: MagicMock) -> None:
    round_id, room_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def start_round(self, *a: object, **kw: object) -> dict:
            return {
                "round_id": round_id,
                "room_id": room_id,
                "song_count": 10,
                "theme": "Pop 90s",
            }

        def start_song(self, *a: object, **kw: object) -> dict:
            return {
                "song_id": uuid4(),
                "round_id": round_id,
                "room_id": room_id,
                "song_index": 0,
                "started_at": _FIXED_NOW,
                "ends_at": _ENDS_AT,
                "preview_url": None,
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    app.dependency_overrides[get_music_provider] = lambda: MagicMock()
    app.dependency_overrides[get_session] = lambda: MagicMock()
    app.dependency_overrides[get_db_factory] = lambda: MagicMock()
    app.dependency_overrides[get_sleep] = lambda: _instant_sleep
    try:
        TestClient(app).post(f"/rooms/{room_id}/rounds", json={"theme": "Pop 90s"})
        calls = mock_manager.broadcast_to_room.call_args_list
        call = next(c for c in calls if c.args[1]["event"] == "round.started")
        d = call.args[1]["data"]
        assert {"round_id", "theme", "song_count"} == set(d.keys())
        assert UUID(d["round_id"]) == round_id
        assert d["theme"] == "Pop 90s"
        assert isinstance(d["song_count"], int)
    finally:
        app.dependency_overrides.clear()


# ── 9. WS song.locked — event shape ───────────────────────────────────────────


def test_song_locked_event_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    song_id, round_id, room_id = uuid4(), uuid4(), uuid4()

    class _FakeRoomService:
        def __init__(self, session: object) -> None:
            pass

        def lock_song(self, sid: UUID) -> dict:
            return {"song_id": song_id, "round_id": round_id}

    monkeypatch.setattr("src.api.deps.RoomService", _FakeRoomService)

    mock_mgr = MagicMock()
    mock_mgr.broadcast_to_room = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value = MagicMock()

    asyncio.run(
        auto_lock_song(song_id, room_id, 0.0, mock_factory, mock_mgr, _instant_sleep)
    )

    call = mock_mgr.broadcast_to_room.call_args
    payload = call.args[1]
    assert payload["event"] == "song.locked"
    assert {"song_id", "round_id"} == set(payload["data"].keys())
    assert payload["data"]["song_id"] == str(song_id)
    assert payload["data"]["round_id"] == str(round_id)


# ── 10. WS song.revealed — event shape ────────────────────────────────────────


def test_song_revealed_event_player_results_shape(mock_manager: MagicMock) -> None:
    pid = uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": uuid4(),
                "room_id": uuid4(),
                "title": "One More Time",
                "artist": "Daft Punk",
                "player_results": [
                    {
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "answer": "one more time",
                        "title_found": True,
                        "artist_found": False,
                        "score": 117,
                    }
                ],
                "mini_leaderboard": [
                    {
                        "rank": 1,
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "total_points": 117,
                    }
                ],
                "round_finished": False,
                "round_leaderboard": [],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        TestClient(app).post(f"/songs/{uuid4()}/reveal", json={"host_id": str(uuid4())})
        calls = mock_manager.broadcast_to_room.call_args_list
        revealed = next(c for c in calls if c.args[1]["event"] == "song.revealed")
        d = revealed.args[1]["data"]
        rev_keys = {"song_id", "title", "artist", "player_results", "mini_leaderboard"}
        assert rev_keys == set(d.keys())
        pr = d["player_results"][0]
        pr_keys = {
            "participant_id", "nickname", "answer",
            "title_found", "artist_found", "score",
        }
        assert pr_keys == set(pr.keys())
        assert isinstance(pr["title_found"], bool)
        assert isinstance(pr["score"], int)
        lb = d["mini_leaderboard"][0]
        assert {"rank", "participant_id", "nickname", "total_points"} == set(lb.keys())
        assert isinstance(lb["rank"], int)
        assert isinstance(lb["total_points"], int)
    finally:
        app.dependency_overrides.clear()


# ── 11. WS round.finished — event shape ───────────────────────────────────────


def test_round_finished_event_shape(mock_manager: MagicMock) -> None:
    pid, room_id = uuid4(), uuid4()

    class _Svc(_BaseService):
        def reveal_song(self, sid: UUID, host_id: UUID) -> dict:
            return {
                "song_id": uuid4(),
                "room_id": room_id,
                "title": "Get Lucky",
                "artist": "Daft Punk",
                "player_results": [],
                "mini_leaderboard": [],
                "round_finished": True,
                "round_leaderboard": [
                    {
                        "rank": 1,
                        "participant_id": str(pid),
                        "nickname": "Alice",
                        "round_points": 200,
                    }
                ],
            }

    app.dependency_overrides[get_room_service] = lambda: _Svc()
    app.dependency_overrides[get_ws_manager] = lambda: mock_manager
    try:
        TestClient(app).post(f"/songs/{uuid4()}/reveal", json={"host_id": str(uuid4())})
        calls = mock_manager.broadcast_to_room.call_args_list
        finished = next(c for c in calls if c.args[1]["event"] == "round.finished")
        d = finished.args[1]["data"]
        assert {"room_id", "round_leaderboard"} == set(d.keys())
        assert d["room_id"] == str(room_id)
        item = d["round_leaderboard"][0]
        rl_keys = {"rank", "participant_id", "nickname", "round_points"}
        assert rl_keys == set(item.keys())
        assert item["rank"] == 1
        assert UUID(item["participant_id"]) == pid
        assert isinstance(item["round_points"], int)
    finally:
        app.dependency_overrides.clear()
