import random
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Optional, TypedDict
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.domain.clock import Clock, UtcClock
from src.domain.entities import Participant, Room, RoomConfig, Round
from src.domain.enums import RoomStatus, RoundStatus, SongStatus, ValidationStatus
from src.domain.exceptions import (
    AnswerNotFoundError,
    InvalidHostTokenError,
    NicknameAlreadyTakenError,
    RoomNotFinishedRoundError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotAcceptingAnswersError,
    SongNotCorrectableError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotLockedError,
    SongNotPlayableError,
    SongNotRevealableError,
)
from src.domain.music_provider import MusicProvider, track_to_song
from src.domain.scoring import compute_song_score
from src.domain.track_selection import select_round_tracks
from src.domain.validation import validate_answer
from src.infrastructure.models import (
    AnswerModel,
    ParticipantModel,
    RoomModel,
    RoundModel,
    ScoreEntryModel,
    SongModel,
)
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider

_LOCKED_STATUSES: frozenset[str] = frozenset(
    {
        SongStatus.LOCKED.value,
        SongStatus.VALIDATION.value,
        SongStatus.REVEALED.value,
        SongStatus.SCORED.value,
    }
)

_CORRECTABLE_STATUSES: frozenset[str] = frozenset(
    {
        SongStatus.LOCKED.value,
        SongStatus.VALIDATION.value,
        SongStatus.REVEALED.value,
    }
)

_REVEALABLE_STATUSES: frozenset[str] = frozenset(
    {SongStatus.LOCKED.value, SongStatus.VALIDATION.value}
)

CODE_CHARS: str = string.ascii_uppercase + string.digits
CODE_LENGTH: int = 6
_MAX_RETRIES: int = 10


class CreateRoomResult(TypedDict):
    room_id: UUID
    code: str
    host_id: UUID
    host_token: str


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
    preview_url: Optional[str]


class LockSongResult(TypedDict):
    song_id: UUID
    round_id: UUID
    room_id: UUID


class SubmitAnswerResult(TypedDict):
    answer_id: UUID
    submitted_at: datetime
    validation_status: str
    title_found: bool
    artist_found: bool


class AnswerSummaryEntry(TypedDict):
    answer_id: UUID
    participant_id: UUID
    nickname: str
    text: str
    validation_status: str
    title_found: bool
    artist_found: bool


class SongSummaryResult(TypedDict):
    song_id: UUID
    title: str
    artist: str
    total_answers: int
    doubtful_count: int
    answers: list[AnswerSummaryEntry]


class OverrideAnswerResult(TypedDict):
    answer_id: UUID
    title_found: bool
    artist_found: bool
    validation_status: str
    score: int


class PlayerRevealEntry(TypedDict):
    participant_id: UUID
    nickname: str
    answer: str
    title_found: bool
    artist_found: bool
    score: int


class MiniLeaderboardEntry(TypedDict):
    rank: int
    participant_id: UUID
    nickname: str
    total_points: int


class RoundLeaderboardEntry(TypedDict):
    rank: int
    participant_id: UUID
    nickname: str
    round_points: int


class RevealSongResult(TypedDict):
    song_id: UUID
    room_id: UUID
    title: str
    artist: str
    player_results: list[PlayerRevealEntry]
    mini_leaderboard: list[MiniLeaderboardEntry]
    round_finished: bool
    round_leaderboard: list[RoundLeaderboardEntry]


_JOINABLE_STATUSES: frozenset[str] = frozenset(
    {RoomStatus.CREATED.value, RoomStatus.WAITING.value}
)


_DEFAULT_ANSWER_DURATION: int = 30


class RoomService:
    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        self._session = session
        self._clock: Clock = clock or UtcClock()

    def _generate_code(self) -> str:
        return "".join(random.choices(CODE_CHARS, k=CODE_LENGTH))

    def _code_exists(self, code: str) -> bool:
        return self._session.query(RoomModel).filter_by(code=code).first() is not None

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
        host_token = secrets.token_urlsafe(32)

        self._session.add(
            RoomModel(
                id=room.id,
                code=room.code,
                status=RoomStatus.CREATED.value,
                host_id=room.host_id,
                host_token=host_token,
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
            host_token=host_token,
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

        if room.status == RoomStatus.CREATED.value:
            room.status = RoomStatus.WAITING.value

        self._session.flush()

        return JoinRoomResult(room_id=room.id, participant_id=participant.id)

    def start_round(
        self, room_id: UUID, host_token: str, theme: str, music_provider: MusicProvider
    ) -> StartRoundResult:
        room = self._session.query(RoomModel).filter_by(id=room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {room_id!r} not found")
        if room.status != RoomStatus.WAITING.value:
            raise RoomNotWaitingError(
                f"Room must be waiting to start a round (status: {room.status!r})"
            )
        if not secrets.compare_digest(room.host_token, host_token):
            raise InvalidHostTokenError(f"Invalid host token for room {room_id!r}")

        config_data: dict[str, Any] = (
            room.config if isinstance(room.config, dict) else {}
        )
        room_config = RoomConfig(
            max_songs_per_round=int(config_data.get("max_songs_per_round", 10)),
            answer_duration_seconds=int(
                config_data.get("answer_duration_seconds", _DEFAULT_ANSWER_DURATION)
            ),
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

        tracks = select_round_tracks(
            theme,
            room_config,
            music_provider,
            StaticFixtureMusicProvider(),
        )
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

        room = self._session.query(RoomModel).filter_by(id=round_.room_id).first()
        answer_duration = (
            int(room.config.get("answer_duration_seconds", _DEFAULT_ANSWER_DURATION))
            if room is not None and isinstance(room.config, dict)
            else _DEFAULT_ANSWER_DURATION
        )

        now = self._clock.now()
        ends_at = now + timedelta(seconds=answer_duration)

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
            preview_url=song.preview_url,
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

    def submit_answer(
        self, song_id: UUID, participant_id: UUID, text: str
    ) -> SubmitAnswerResult:
        song = self._session.query(SongModel).filter_by(id=song_id).first()
        if song is None:
            raise SongNotFoundError(f"Song {song_id!r} not found")
        if song.status != SongStatus.PLAYING.value:
            raise SongNotAcceptingAnswersError(
                f"Song is not accepting answers (status: {song.status!r})"
            )

        now = self._clock.now()
        validation = validate_answer(
            text, song.title, song.artist, song.aliases_title, song.aliases_artist
        )

        title_found = validation.title == ValidationStatus.FOUND
        artist_found = validation.artist == ValidationStatus.FOUND

        if (
            validation.title == ValidationStatus.FOUND
            or validation.artist == ValidationStatus.FOUND
        ):
            overall = ValidationStatus.FOUND
        elif (
            validation.title == ValidationStatus.DOUBTFUL
            or validation.artist == ValidationStatus.DOUBTFUL
        ):
            overall = ValidationStatus.DOUBTFUL
        else:
            overall = ValidationStatus.NOT_FOUND

        answer_id = uuid4()
        self._session.add(
            AnswerModel(
                id=answer_id,
                song_id=song_id,
                participant_id=participant_id,
                text=text,
                submitted_at=now,
                title_found=title_found,
                artist_found=artist_found,
                validation_status=overall.value,
                host_override=None,
            )
        )
        self._session.flush()

        return SubmitAnswerResult(
            answer_id=answer_id,
            submitted_at=now,
            validation_status=overall.value,
            title_found=title_found,
            artist_found=artist_found,
        )

    def get_song_summary(self, song_id: UUID, host_token: str) -> SongSummaryResult:
        song = self._session.query(SongModel).filter_by(id=song_id).first()
        if song is None:
            raise SongNotFoundError(f"Song {song_id!r} not found")
        if song.status not in _LOCKED_STATUSES:
            raise SongNotLockedError(
                f"Song is not locked yet (status: {song.status!r})"
            )

        round_ = self._session.query(RoundModel).filter_by(id=song.round_id).first()
        if round_ is None:
            raise RoundNotFoundError(f"Round {song.round_id!r} not found")

        room = self._session.query(RoomModel).filter_by(id=round_.room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {round_.room_id!r} not found")

        if not secrets.compare_digest(room.host_token, host_token):
            raise InvalidHostTokenError(f"Invalid host token for song {song_id!r}")

        raw_answers = self._session.query(AnswerModel).filter_by(song_id=song_id).all()

        entries: list[AnswerSummaryEntry] = []
        doubtful_count = 0
        for ans in raw_answers:
            participant = (
                self._session.query(ParticipantModel)
                .filter_by(id=ans.participant_id)
                .first()
            )
            nickname = participant.nickname if participant else "Unknown"
            if ans.validation_status == ValidationStatus.DOUBTFUL.value:
                doubtful_count += 1
            entries.append(
                AnswerSummaryEntry(
                    answer_id=ans.id,
                    participant_id=ans.participant_id,
                    nickname=nickname,
                    text=ans.text,
                    validation_status=ans.validation_status,
                    title_found=ans.title_found,
                    artist_found=ans.artist_found,
                )
            )

        return SongSummaryResult(
            song_id=song.id,
            title=song.title,
            artist=song.artist,
            total_answers=len(entries),
            doubtful_count=doubtful_count,
            answers=entries,
        )

    def override_answer(
        self,
        song_id: UUID,
        answer_id: UUID,
        host_token: str,
        title_accepted: bool,
        artist_accepted: bool,
    ) -> OverrideAnswerResult:
        song = self._session.query(SongModel).filter_by(id=song_id).first()
        if song is None:
            raise SongNotFoundError(f"Song {song_id!r} not found")
        if song.status not in _CORRECTABLE_STATUSES:
            raise SongNotCorrectableError(
                f"Song is not correctable (status: {song.status!r})"
            )

        round_ = self._session.query(RoundModel).filter_by(id=song.round_id).first()
        if round_ is None:
            raise RoundNotFoundError(f"Round {song.round_id!r} not found")

        room = self._session.query(RoomModel).filter_by(id=round_.room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {round_.room_id!r} not found")
        if not secrets.compare_digest(room.host_token, host_token):
            raise InvalidHostTokenError(f"Invalid host token for song {song_id!r}")

        answer = (
            self._session.query(AnswerModel)
            .filter_by(id=answer_id, song_id=song_id)
            .first()
        )
        if answer is None:
            raise AnswerNotFoundError(
                f"Answer {answer_id!r} not found for song {song_id!r}"
            )

        answer.title_found = title_accepted
        answer.artist_found = artist_accepted
        if title_accepted or artist_accepted:
            answer.validation_status = ValidationStatus.FOUND.value
            answer.host_override = ValidationStatus.FOUND.value
        else:
            answer.validation_status = ValidationStatus.NOT_FOUND.value
            answer.host_override = ValidationStatus.NOT_FOUND.value

        time_remaining = 0.0
        total_seconds = 0.0
        if song.started_at and song.ends_at:
            total_seconds = max(0.0, (song.ends_at - song.started_at).total_seconds())
            time_remaining = max(
                0.0, (song.ends_at - answer.submitted_at).total_seconds()
            )

        score = compute_song_score(
            title_accepted, artist_accepted, time_remaining, total_seconds
        )

        score_entry = (
            self._session.query(ScoreEntryModel)
            .filter_by(participant_id=answer.participant_id, song_id=song_id)
            .first()
        )
        if score_entry is None:
            self._session.add(
                ScoreEntryModel(
                    id=uuid4(),
                    participant_id=answer.participant_id,
                    room_id=round_.room_id,
                    song_id=song_id,
                    round_id=round_.id,
                    points=score,
                )
            )
        else:
            score_entry.points = score

        self._session.flush()

        return OverrideAnswerResult(
            answer_id=answer_id,
            title_found=title_accepted,
            artist_found=artist_accepted,
            validation_status=answer.validation_status,
            score=score,
        )

    def reveal_song(self, song_id: UUID, host_token: str) -> RevealSongResult:
        song = self._session.query(SongModel).filter_by(id=song_id).first()
        if song is None:
            raise SongNotFoundError(f"Song {song_id!r} not found")
        if song.status not in _REVEALABLE_STATUSES:
            raise SongNotRevealableError(
                f"Song cannot be revealed (status: {song.status!r})"
            )

        round_ = self._session.query(RoundModel).filter_by(id=song.round_id).first()
        if round_ is None:
            raise RoundNotFoundError(f"Round {song.round_id!r} not found")

        room = self._session.query(RoomModel).filter_by(id=round_.room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {round_.room_id!r} not found")
        if not secrets.compare_digest(room.host_token, host_token):
            raise InvalidHostTokenError(f"Invalid host token for song {song_id!r}")

        song.status = SongStatus.REVEALED.value
        self._session.flush()

        songs_in_round = (
            self._session.query(SongModel).filter_by(round_id=round_.id).all()
        )
        _done = frozenset({SongStatus.REVEALED.value, SongStatus.SCORED.value})
        total_songs = len(songs_in_round)
        revealed_count = sum(1 for s in songs_in_round if s.status in _done)
        round_finished = total_songs > 0 and revealed_count == total_songs

        if round_finished:
            round_.status = RoundStatus.FINISHED.value
            room.status = RoomStatus.ROUND_FINISHED.value
        elif room.status == RoomStatus.ROUND_IN_PROGRESS.value:
            room.status = RoomStatus.REVEAL.value
        self._session.flush()

        raw_answers = self._session.query(AnswerModel).filter_by(song_id=song_id).all()

        player_results: list[PlayerRevealEntry] = []
        for ans in raw_answers:
            participant = (
                self._session.query(ParticipantModel)
                .filter_by(id=ans.participant_id)
                .first()
            )
            nickname = participant.nickname if participant else "Unknown"
            score_entry = (
                self._session.query(ScoreEntryModel)
                .filter_by(participant_id=ans.participant_id, song_id=song_id)
                .first()
            )
            points = score_entry.points if score_entry else 0
            player_results.append(
                PlayerRevealEntry(
                    participant_id=ans.participant_id,
                    nickname=nickname,
                    answer=ans.text,
                    title_found=ans.title_found,
                    artist_found=ans.artist_found,
                    score=points,
                )
            )

        all_score_entries = (
            self._session.query(ScoreEntryModel).filter_by(room_id=round_.room_id).all()
        )
        totals: dict[UUID, int] = {}
        for se in all_score_entries:
            pid = se.participant_id
            totals[pid] = totals.get(pid, 0) + se.points

        sorted_pairs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        mini_leaderboard: list[MiniLeaderboardEntry] = []
        for i, (pid, pts) in enumerate(sorted_pairs):
            participant = (
                self._session.query(ParticipantModel).filter_by(id=pid).first()
            )
            nickname = participant.nickname if participant else "Unknown"
            if i > 0 and pts == sorted_pairs[i - 1][1]:
                rank = mini_leaderboard[-1]["rank"]
            else:
                rank = i + 1
            mini_leaderboard.append(
                MiniLeaderboardEntry(
                    rank=rank,
                    participant_id=pid,
                    nickname=nickname,
                    total_points=pts,
                )
            )

        round_leaderboard: list[RoundLeaderboardEntry] = []
        if round_finished:
            round_score_entries = (
                self._session.query(ScoreEntryModel).filter_by(round_id=round_.id).all()
            )
            round_totals: dict[UUID, int] = {}
            for se in round_score_entries:
                pid = se.participant_id
                round_totals[pid] = round_totals.get(pid, 0) + se.points

            round_sorted = sorted(
                round_totals.items(), key=lambda x: x[1], reverse=True
            )
            for i, (pid, pts) in enumerate(round_sorted):
                participant = (
                    self._session.query(ParticipantModel).filter_by(id=pid).first()
                )
                nickname = participant.nickname if participant else "Unknown"
                if i > 0 and pts == round_sorted[i - 1][1]:
                    rank = round_leaderboard[-1]["rank"]
                else:
                    rank = i + 1
                round_leaderboard.append(
                    RoundLeaderboardEntry(
                        rank=rank,
                        participant_id=pid,
                        nickname=nickname,
                        round_points=pts,
                    )
                )

        return RevealSongResult(
            song_id=song.id,
            room_id=round_.room_id,
            title=song.title,
            artist=song.artist,
            player_results=player_results,
            mini_leaderboard=mini_leaderboard,
            round_finished=round_finished,
            round_leaderboard=round_leaderboard,
        )

    def restart_round(
        self, room_id: UUID, host_token: str, theme: str, music_provider: MusicProvider
    ) -> StartRoundResult:
        room = self._session.query(RoomModel).filter_by(id=room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Room {room_id!r} not found")
        if room.status != RoomStatus.ROUND_FINISHED.value:
            raise RoomNotFinishedRoundError(
                f"Room must be in round_finished to restart (status: {room.status!r})"
            )
        if not secrets.compare_digest(room.host_token, host_token):
            raise InvalidHostTokenError(f"Invalid host token for room {room_id!r}")
        room.status = RoomStatus.WAITING.value
        self._session.flush()
        return self.start_round(room_id, host_token, theme, music_provider)
