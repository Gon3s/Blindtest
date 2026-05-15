from unittest.mock import MagicMock

import pytest

from src.application.room_service import CODE_CHARS, CODE_LENGTH, RoomService
from src.infrastructure.models import RoomModel


@pytest.fixture
def session() -> MagicMock:
    mock = MagicMock()
    # No existing room with any code by default
    mock.query.return_value.filter_by.return_value.first.return_value = None
    return mock


@pytest.fixture
def service(session: MagicMock) -> RoomService:
    return RoomService(session)


def test_create_room_returns_room_id_and_code(service: RoomService) -> None:
    result = service.create_room("Alice")
    assert "room_id" in result
    assert "code" in result
    assert "host_id" in result


def test_create_room_code_is_correct_length(service: RoomService) -> None:
    result = service.create_room("Alice")
    assert len(result["code"]) == CODE_LENGTH


def test_create_room_code_uses_valid_chars(service: RoomService) -> None:
    result = service.create_room("Alice")
    for ch in result["code"]:
        assert ch in CODE_CHARS


def test_create_room_default_config_persisted(
    service: RoomService, session: MagicMock
) -> None:
    service.create_room("Alice")
    added_models = [call.args[0] for call in session.add.call_args_list]
    room_model = next(m for m in added_models if isinstance(m, RoomModel))
    assert room_model.config["max_songs_per_round"] == 10
    assert room_model.config["answer_duration_seconds"] == 30


def test_create_room_host_participant_is_host(
    service: RoomService, session: MagicMock
) -> None:
    from src.infrastructure.models import ParticipantModel

    service.create_room("Alice")
    added_models = [call.args[0] for call in session.add.call_args_list]
    participant = next(m for m in added_models if isinstance(m, ParticipantModel))
    assert participant.is_host is True
    assert participant.nickname == "Alice"


def test_create_room_retries_on_code_collision(session: MagicMock) -> None:
    existing = MagicMock(spec=RoomModel)
    # First two calls return existing room (collision), third returns None (free code)
    session.query.return_value.filter_by.return_value.first.side_effect = [
        existing,
        existing,
        None,
    ]
    service = RoomService(session)
    result = service.create_room("Bob")
    assert "code" in result
