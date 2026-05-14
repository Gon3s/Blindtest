from uuid import uuid4

import pytest

from src.domain.entities import Room
from src.domain.enums import RoomStatus
from src.domain.exceptions import RoomTransitionError


class TestRoomValidTransitions:
    def test_open_created_to_waiting(self) -> None:
        room = Room(host_id=uuid4())
        room.open()
        assert room.status == RoomStatus.WAITING

    def test_start_round_waiting_to_round_in_progress(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.WAITING)
        room.start_round()
        assert room.status == RoomStatus.ROUND_IN_PROGRESS

    def test_start_reveal_round_in_progress_to_reveal(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_IN_PROGRESS)
        room.start_reveal()
        assert room.status == RoomStatus.REVEAL

    def test_finish_round_reveal_to_round_finished(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.REVEAL)
        room.finish_round()
        assert room.status == RoomStatus.ROUND_FINISHED

    def test_restart_round_finished_to_waiting(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_FINISHED)
        room.restart()
        assert room.status == RoomStatus.WAITING

    def test_close_from_waiting(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.WAITING)
        room.close()
        assert room.status == RoomStatus.FINISHED

    def test_close_from_round_finished(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_FINISHED)
        room.close()
        assert room.status == RoomStatus.FINISHED


class TestRoomInvalidTransitions:
    def test_created_cannot_start_round(self) -> None:
        room = Room(host_id=uuid4())
        with pytest.raises(RoomTransitionError):
            room.start_round()

    def test_created_cannot_close(self) -> None:
        room = Room(host_id=uuid4())
        with pytest.raises(RoomTransitionError):
            room.close()

    def test_created_cannot_start_reveal(self) -> None:
        room = Room(host_id=uuid4())
        with pytest.raises(RoomTransitionError):
            room.start_reveal()

    def test_waiting_cannot_start_reveal(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.WAITING)
        with pytest.raises(RoomTransitionError):
            room.start_reveal()

    def test_waiting_cannot_finish_round(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.WAITING)
        with pytest.raises(RoomTransitionError):
            room.finish_round()

    def test_round_in_progress_cannot_open(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_IN_PROGRESS)
        with pytest.raises(RoomTransitionError):
            room.open()

    def test_round_in_progress_cannot_restart(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_IN_PROGRESS)
        with pytest.raises(RoomTransitionError):
            room.restart()

    def test_round_in_progress_cannot_close(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.ROUND_IN_PROGRESS)
        with pytest.raises(RoomTransitionError):
            room.close()

    def test_reveal_cannot_open(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.REVEAL)
        with pytest.raises(RoomTransitionError):
            room.open()

    def test_reveal_cannot_close(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.REVEAL)
        with pytest.raises(RoomTransitionError):
            room.close()

    def test_finished_cannot_open(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.FINISHED)
        with pytest.raises(RoomTransitionError):
            room.open()

    def test_finished_cannot_start_round(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.FINISHED)
        with pytest.raises(RoomTransitionError):
            room.start_round()

    def test_finished_cannot_restart(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.FINISHED)
        with pytest.raises(RoomTransitionError):
            room.restart()

    def test_error_message_contains_states(self) -> None:
        room = Room(host_id=uuid4())
        with pytest.raises(RoomTransitionError, match="created"):
            room.start_round()


class TestRoomFinalState:
    def test_finished_room_is_terminal(self) -> None:
        room = Room(host_id=uuid4(), status=RoomStatus.FINISHED)
        assert room.status == RoomStatus.FINISHED

    def test_full_lifecycle_single_round(self) -> None:
        room = Room(host_id=uuid4())
        room.open()
        room.start_round()
        room.start_reveal()
        room.finish_round()
        room.close()
        assert room.status == RoomStatus.FINISHED

    def test_full_lifecycle_two_rounds(self) -> None:
        room = Room(host_id=uuid4())
        room.open()
        room.start_round()
        room.start_reveal()
        room.finish_round()
        room.restart()
        room.start_round()
        room.start_reveal()
        room.finish_round()
        room.close()
        assert room.status == RoomStatus.FINISHED
