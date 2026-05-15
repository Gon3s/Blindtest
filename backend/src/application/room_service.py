import random
import string
from typing import TypedDict
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.domain.entities import Participant, Room, RoomConfig
from src.domain.enums import RoomStatus
from src.domain.exceptions import (
    NicknameAlreadyTakenError,
    RoomNotFoundError,
    RoomNotJoinableError,
)
from src.infrastructure.models import ParticipantModel, RoomModel

CODE_CHARS: str = string.ascii_uppercase + string.digits
CODE_LENGTH: int = 6
_MAX_RETRIES: int = 10


class CreateRoomResult(TypedDict):
    room_id: UUID
    code: str
    host_id: UUID


class JoinRoomResult(TypedDict):
    room_id: UUID
    participant_id: UUID


_JOINABLE_STATUSES: frozenset[str] = frozenset(
    {RoomStatus.CREATED.value, RoomStatus.WAITING.value}
)


class RoomService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _generate_code(self) -> str:
        return "".join(random.choices(CODE_CHARS, k=CODE_LENGTH))

    def _code_exists(self, code: str) -> bool:
        return (
            self._session.query(RoomModel).filter_by(code=code).first() is not None
        )

    def create_room(self, host_nickname: str) -> CreateRoomResult:
        code = self._generate_code()
        retries = 0
        while self._code_exists(code) and retries < _MAX_RETRIES:
            code = self._generate_code()
            retries += 1

        participant_id = uuid4()
        config = RoomConfig()
        room = Room(host_id=participant_id, code=code, config=config)
        participant = Participant(
            id=participant_id,
            nickname=host_nickname,
            room_id=room.id,
            is_host=True,
        )

        self._session.add(
            RoomModel(
                id=room.id,
                code=room.code,
                status=RoomStatus.CREATED.value,
                host_id=room.host_id,
                config={
                    "max_songs_per_round": config.max_songs_per_round,
                    "answer_duration_seconds": config.answer_duration_seconds,
                },
            )
        )
        # Flush the room before the participant so the FK constraint is satisfied.
        # The models have no ORM relationship(), so SQLAlchemy cannot infer the order.
        self._session.flush()
        self._session.add(
            ParticipantModel(
                id=participant.id,
                nickname=participant.nickname,
                room_id=participant.room_id,
                is_host=participant.is_host,
            )
        )
        self._session.flush()

        return CreateRoomResult(
            room_id=room.id,
            code=room.code,
            host_id=participant.id,
        )

    def join_room(self, code: str, nickname: str) -> JoinRoomResult:
        room = self._session.query(RoomModel).filter_by(code=code).first()
        if room is None:
            raise RoomNotFoundError(f"Room with code {code!r} not found")
        if room.status not in _JOINABLE_STATUSES:
            raise RoomNotJoinableError(
                f"Room is not joinable (status: {room.status!r})"
            )
        existing = (
            self._session.query(ParticipantModel)
            .filter_by(room_id=room.id, nickname=nickname)
            .first()
        )
        if existing is not None:
            raise NicknameAlreadyTakenError(
                f"Nickname {nickname!r} is already taken in this room"
            )

        participant = Participant(nickname=nickname, room_id=room.id)
        self._session.add(
            ParticipantModel(
                id=participant.id,
                nickname=participant.nickname,
                room_id=participant.room_id,
                is_host=False,
            )
        )
        self._session.flush()

        return JoinRoomResult(room_id=room.id, participant_id=participant.id)
