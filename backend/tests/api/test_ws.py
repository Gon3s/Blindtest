from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.infrastructure.db import get_db
from src.main import app


class _FakeSession:
    def query(self, model: type) -> "_FakeSession":
        return self

    def filter_by(self, **kwargs: object) -> "_FakeSession":
        return self

    def all(self) -> list[object]:
        return []

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def _fake_db() -> Generator[_FakeSession, None, None]:
    yield _FakeSession()


class _FakeJoinService:
    def __init__(self, room_id: UUID, participant_id: UUID) -> None:
        self._room_id = room_id
        self._participant_id = participant_id

    def create_room(self, host_nickname: str) -> dict[str, object]:
        return {}

    def join_room(self, code: str, nickname: str) -> dict[str, object]:
        return {"room_id": self._room_id, "participant_id": self._participant_id}


@pytest.fixture
def ws_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = _fake_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_websocket_connect_receives_room_state(ws_client: TestClient) -> None:
    room_id = uuid4()
    with ws_client.websocket_connect(f"/ws/rooms/{room_id}") as ws:
        data = ws.receive_json()
    assert data["event"] == "room.state"


def test_websocket_room_state_contains_room_id(ws_client: TestClient) -> None:
    room_id = uuid4()
    with ws_client.websocket_connect(f"/ws/rooms/{room_id}") as ws:
        data = ws.receive_json()
    assert data["data"]["room_id"] == str(room_id)


def test_websocket_room_state_contains_participants_list(ws_client: TestClient) -> None:
    room_id = uuid4()
    with ws_client.websocket_connect(f"/ws/rooms/{room_id}") as ws:
        data = ws.receive_json()
    assert data["data"]["participants"] == []


def test_join_room_broadcasts_participant_joined(ws_client: TestClient) -> None:
    room_id = uuid4()
    participant_id = uuid4()

    app.dependency_overrides[get_room_service] = lambda: _FakeJoinService(
        room_id, participant_id
    )

    with ws_client.websocket_connect(f"/ws/rooms/{room_id}") as ws:
        ws.receive_json()  # consume room.state
        ws_client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        data = ws.receive_json()

    assert data["event"] == "participant.joined"
    assert data["data"]["nickname"] == "Bob"
    assert data["data"]["participant_id"] == str(participant_id)
