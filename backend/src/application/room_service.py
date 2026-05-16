import random
import string
from datetime import datetime, timedelta
from typing import TypedDict
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.domain.clock import Clock, UtcClock
from src.domain.entities import Participant, Room, RoomConfig, Round
from src.domain.enums import RoomStatus, RoundStatus, SongStatus
from src.domain.exceptions import (
    NicknameAlreadyTakenError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotPlayableError,
)
from src.domain.music_provider import MusicProvider, track_to_song
from src.infrastructure.models import ParticipantModel, RoomModel, RoundModel, SongModel

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


class StartRoundResult(TypedDict):
    round_id: UUID
    room_id: UUID
    song_count: int
    theme: str


class StartSongResult(TypedDict):
    song_id: UUID
    round_id: UUID
    room_id: UUID
    song_index: int
    started_at: datetime
    ends_at: datetime


class LockSongResult(TypedDict):
    song_id: UUID
    round_id: UUID
    room_id: UUID


_JOINABLE_STATUSES: frozenset[str] = frozenset(
    {RoomStatus.CREATED.value, RoomStatus.WAITING.value}
)


_SONG_DURATION_SECONDS: int = 30


class RoomService:
    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        self._session = session
        self._clock: Clock = clock or UtcClock()

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

    def start_round(
        self, room_id: UUID, theme: str, music_provider: MusicProvider
    ) -> StartRoundResult:
        room = self._session.query(RoomModel).filter_by(id=room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {room_id!r} not found")
        if room.status != RoomStatus.WAITING.value:
            raise RoomNotWaitingError(
                f"Room must be waiting to start a round (status: {room.status!r})"
            )

        round_index: int = (
            self._session.query(RoundModel).filter_by(room_id=room_id).count()
        )
        round_entity = Round(
            room_id=room_id,
            index=round_index,
            theme=theme,
            status=RoundStatus.IN_PROGRESS,
        )

        tracks = music_provider.search(theme, limit=10)
        songs = [
            track_to_song(track, round_entity.id, idx)
            for idx, track in enumerate(tracks)
        ]

        self._session.add(
            RoundModel(
                id=round_entity.id,
                room_id=room_id,
                index=round_entity.index,
                theme=theme,
                status=RoundStatus.IN_PROGRESS.value,
            )
        )
        self._session.flush()

        for song in songs:
            self._session.add(
                SongModel(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    round_id=song.round_id,
                    index=song.index,
                    aliases_title=song.aliases_title,
                    aliases_artist=song.aliases_artist,
                    preview_url=song.preview_url,
                    status=song.status.value,
                    started_at=song.started_at,
                    ends_at=song.ends_at,
                )
            )
        self._session.flush()

        room.status = RoomStatus.ROUND_IN_PROGRESS.value
        self._session.flush()

        return StartRoundResult(
            round_id=round_entity.id,
            room_id=room_id,
            song_count=len(songs),
            theme=theme,
        )

    def start_song(self, round_id: UUID, song_index: int) -> StartSongResult:
        round_ = self._session.query(RoundModel).filter_by(id=round_id).first()
        if round_ is None:
            raise RoundNotFoundError(f"Round {round_id!r} not found")
        if round_.status != RoundStatus.IN_PROGRESS.value:
            raise RoundNotInProgressError(
                f"Round is not in progress (status: {round_.status!r})"
            )

        song = (
            self._session.query(SongModel)
            .filter_by(round_id=round_id, index=song_index)
            .first()
        )
        if song is None:
            raise SongNotFoundError(
                f"Song at index {song_index} not found in round {round_id!r}"
            )
        if song.status != SongStatus.UPCOMING.value:
            raise SongNotPlayableError(
                f"Song is not playable (status: {song.status!r})"
            )

        now = self._clock.now()
        ends_at = now + timedelta(seconds=_SONG_DURATION_SECONDS)

        song.status = SongStatus.PLAYING.value
        song.started_at = now
        song.ends_at = ends_at
        self._session.flush()

        return StartSongResult(
            song_id=song.id,
            round_id=round_id,
            room_id=round_.room_id,
            song_index=song_index,
            started_at=now,
            ends_at=ends_at,
        )

    def lock_song(self, song_id: UUID) -> LockSongResult:
        song = self._session.query(SongModel).filter_by(id=song_id).first()
        if song is None:
            raise SongNotFoundError(f"Song {song_id!r} not found")
        if song.status != SongStatus.PLAYING.value:
            raise SongNotLockableError(
                f"Song cannot be locked (status: {song.status!r})"
            )

        round_ = self._session.query(RoundModel).filter_by(id=song.round_id).first()
        if round_ is None:
            raise RoundNotFoundError(f"Round {song.round_id!r} not found")

        song.status = SongStatus.LOCKED.value
        self._session.flush()

        return LockSongResult(
            song_id=song_id,
            round_id=song.round_id,
            room_id=round_.room_id,
        )
