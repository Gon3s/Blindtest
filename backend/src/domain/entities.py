from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from .enums import RoomStatus, RoundStatus, SongStatus, ValidationStatus
from .exceptions import RoomTransitionError

_ROOM_TRANSITIONS: dict[RoomStatus, set[RoomStatus]] = {
    RoomStatus.CREATED: {RoomStatus.WAITING},
    RoomStatus.WAITING: {RoomStatus.ROUND_IN_PROGRESS, RoomStatus.FINISHED},
    RoomStatus.ROUND_IN_PROGRESS: {RoomStatus.REVEAL},
    RoomStatus.REVEAL: {RoomStatus.ROUND_FINISHED},
    RoomStatus.ROUND_FINISHED: {RoomStatus.WAITING, RoomStatus.FINISHED},
    RoomStatus.FINISHED: set(),
}


@dataclass
class RoomConfig:
    max_songs_per_round: int = 10
    answer_duration_seconds: int = 30


@dataclass
class Participant:
    nickname: str
    room_id: UUID
    id: UUID = field(default_factory=uuid4)
    team_id: Optional[UUID] = None
    is_host: bool = False


@dataclass
class Team:
    name: str
    room_id: UUID
    id: UUID = field(default_factory=uuid4)
    member_ids: list[UUID] = field(default_factory=list)


@dataclass
class Room:
    host_id: UUID
    id: UUID = field(default_factory=uuid4)
    code: str = ""
    status: RoomStatus = RoomStatus.CREATED
    config: RoomConfig = field(default_factory=RoomConfig)
    participant_ids: list[UUID] = field(default_factory=list)
    team_ids: list[UUID] = field(default_factory=list)
    round_ids: list[UUID] = field(default_factory=list)

    def _transition(self, target: RoomStatus) -> None:
        if target not in _ROOM_TRANSITIONS[self.status]:
            raise RoomTransitionError(
                f"Cannot transition from {self.status.value!r} to {target.value!r}"
            )
        self.status = target

    def open(self) -> None:
        self._transition(RoomStatus.WAITING)

    def start_round(self) -> None:
        self._transition(RoomStatus.ROUND_IN_PROGRESS)

    def start_reveal(self) -> None:
        self._transition(RoomStatus.REVEAL)

    def finish_round(self) -> None:
        self._transition(RoomStatus.ROUND_FINISHED)

    def restart(self) -> None:
        self._transition(RoomStatus.WAITING)

    def close(self) -> None:
        self._transition(RoomStatus.FINISHED)


@dataclass
class Round:
    room_id: UUID
    index: int
    theme: str
    id: UUID = field(default_factory=uuid4)
    status: RoundStatus = RoundStatus.PENDING
    song_ids: list[UUID] = field(default_factory=list)


@dataclass
class Song:
    title: str
    artist: str
    round_id: UUID
    index: int
    id: UUID = field(default_factory=uuid4)
    aliases_title: list[str] = field(default_factory=list)
    aliases_artist: list[str] = field(default_factory=list)
    preview_url: Optional[str] = None
    status: SongStatus = SongStatus.UPCOMING
    started_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


@dataclass
class Answer:
    song_id: UUID
    participant_id: UUID
    text: str
    submitted_at: datetime
    id: UUID = field(default_factory=uuid4)
    title_found: bool = False
    artist_found: bool = False
    validation_status: ValidationStatus = ValidationStatus.NOT_FOUND
    host_override: Optional[ValidationStatus] = None


@dataclass
class ScoreEntry:
    participant_id: UUID
    room_id: UUID
    points: int
    id: UUID = field(default_factory=uuid4)
    song_id: Optional[UUID] = None
    round_id: Optional[UUID] = None
