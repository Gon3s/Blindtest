from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.domain.exceptions import (
    NicknameAlreadyTakenError,
    RoomNotFoundError,
    RoomNotJoinableError,
)
from src.main import app


class _FakeRoomService:
    def __init__(self, result: dict) -> None:
        self._result = result

    def create_room(self, host_nickname: str) -> dict:
        return self._result

    def join_room(self, code: str, nickname: str) -> dict:
        return self._result


@pytest.fixture
def room_result() -> dict:
    return {
        "room_id": uuid4(),
        "code": "ABC123",
        "host_id": uuid4(),
        "host_token": "test-host-token-xyz",
    }


@pytest.fixture
def client_with_service(room_result: dict) -> TestClient:
    fake = _FakeRoomService(room_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_room_returns_201(client_with_service: TestClient) -> None:
    response = client_with_service.post("/rooms", json={"host_nickname": "Alice"})
    assert response.status_code == 201


def test_create_room_returns_room_id_and_code(
    client_with_service: TestClient, room_result: dict
) -> None:
    response = client_with_service.post("/rooms", json={"host_nickname": "Alice"})
    data = response.json()
    assert UUID(data["room_id"]) == room_result["room_id"]
    assert data["code"] == room_result["code"]


def test_create_room_missing_nickname_returns_422(
    client_with_service: TestClient,
) -> None:
    response = client_with_service.post("/rooms", json={})
    assert response.status_code == 422


def test_create_room_empty_nickname_returns_422(
    client_with_service: TestClient,
) -> None:
    response = client_with_service.post("/rooms", json={"host_nickname": ""})
    assert response.status_code == 422


# --- join room ---


@pytest.fixture
def join_result() -> dict:
    return {
        "room_id": uuid4(),
        "participant_id": uuid4(),
    }


@pytest.fixture
def join_client(join_result: dict) -> TestClient:
    fake = _FakeRoomService(join_result)
    app.dependency_overrides[get_room_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_join_room_returns_201(join_client: TestClient) -> None:
    response = join_client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
    assert response.status_code == 201


def test_join_room_returns_room_id_and_participant_id(
    join_client: TestClient, join_result: dict
) -> None:
    response = join_client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
    data = response.json()
    assert UUID(data["room_id"]) == join_result["room_id"]
    assert UUID(data["participant_id"]) == join_result["participant_id"]


def test_join_room_empty_nickname_returns_422(join_client: TestClient) -> None:
    response = join_client.post("/rooms/ABC123/join", json={"nickname": ""})
    assert response.status_code == 422


def test_join_room_missing_nickname_returns_422(join_client: TestClient) -> None:
    response = join_client.post("/rooms/ABC123/join", json={})
    assert response.status_code == 422


def test_join_room_not_found_returns_404() -> None:
    class _NotFoundService:
        def create_room(self, host_nickname: str) -> dict:
            return {}

        def join_room(self, code: str, nickname: str) -> dict:
            raise RoomNotFoundError("not found")

    app.dependency_overrides[get_room_service] = lambda: _NotFoundService()
    try:
        client = TestClient(app)
        response = client.post("/rooms/XXXXXX/join", json={"nickname": "Bob"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_join_room_not_joinable_returns_409() -> None:
    class _NotJoinableService:
        def create_room(self, host_nickname: str) -> dict:
            return {}

        def join_room(self, code: str, nickname: str) -> dict:
            raise RoomNotJoinableError("not joinable")

    app.dependency_overrides[get_room_service] = lambda: _NotJoinableService()
    try:
        client = TestClient(app)
        response = client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_join_room_nickname_taken_returns_409() -> None:
    class _NicknameTakenService:
        def create_room(self, host_nickname: str) -> dict:
            return {}

        def join_room(self, code: str, nickname: str) -> dict:
            raise NicknameAlreadyTakenError("taken")

    app.dependency_overrides[get_room_service] = lambda: _NicknameTakenService()
    try:
        client = TestClient(app)
        response = client.post("/rooms/ABC123/join", json={"nickname": "Bob"})
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
