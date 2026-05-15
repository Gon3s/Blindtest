from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.routes.rooms import get_room_service
from src.main import app


class _FakeRoomService:
    def __init__(self, result: dict) -> None:
        self._result = result

    def create_room(self, host_nickname: str) -> dict:
        return self._result


@pytest.fixture
def room_result() -> dict:
    return {
        "room_id": uuid4(),
        "code": "ABC123",
        "host_id": uuid4(),
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
