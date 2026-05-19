"""TDD — T-034: enchaîner les 10 chansons, fin de manche, classement manche."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import RoomStatus, RoundStatus, SongStatus
from src.domain.exceptions import RoundNotInProgressError
from src.infrastructure.models import (
    AnswerModel,
    ParticipantModel,
    RoomModel,
    RoundModel,
    ScoreEntryModel,
    SongModel,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _song_mock(
    song_id: UUID,
    round_id: UUID,
    index: int,
    status: str = SongStatus.LOCKED.value,
) -> MagicMock:
    s = MagicMock(spec=SongModel)
    s.id = song_id
    s.round_id = round_id
    s.index = index
    s.status = status
    s.title = f"Song {index}"
    s.artist = f"Artist {index}"
    return s


def _round_mock(
    round_id: UUID,
    room_id: UUID,
    status: str = RoundStatus.IN_PROGRESS.value,
) -> MagicMock:
    r = MagicMock(spec=RoundModel)
    r.id = round_id
    r.room_id = room_id
    r.status = status
    return r


def _room_mock(room_id: UUID, host_token: str) -> MagicMock:
    r = MagicMock(spec=RoomModel)
    r.id = room_id
    r.host_token = host_token
    r.status = RoomStatus.ROUND_IN_PROGRESS.value
    return r


def _score_entry_mock(
    participant_id: UUID, room_id: UUID, round_id: UUID, song_id: UUID, points: int
) -> MagicMock:
    se = MagicMock(spec=ScoreEntryModel)
    se.id = uuid4()
    se.participant_id = participant_id
    se.room_id = room_id
    se.round_id = round_id
    se.song_id = song_id
    se.points = points
    return se


def _participant_mock(pid: UUID, nickname: str) -> MagicMock:
    p = MagicMock(spec=ParticipantModel)
    p.id = pid
    p.nickname = nickname
    return p


def _build_session(
    current_song: MagicMock,
    all_songs_in_round: list[MagicMock],
    round_: MagicMock,
    room: MagicMock,
    participants: list[MagicMock],
    room_score_entries: list[MagicMock] | None = None,
    round_score_entries: list[MagicMock] | None = None,
) -> MagicMock:
    pmap = {p.id: p for p in participants}
    _room_se = room_score_entries or []
    _round_se = round_score_entries or []

    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:

            def _song_filter(**kw: object) -> MagicMock:
                inner = MagicMock()
                if "id" in kw:
                    inner.first.return_value = current_song
                    inner.all.return_value = [current_song]
                elif "round_id" in kw:
                    inner.first.return_value = None
                    inner.all.return_value = all_songs_in_round
                else:
                    inner.first.return_value = None
                    inner.all.return_value = []
                return inner

            q.filter_by.side_effect = _song_filter
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        elif model is AnswerModel:
            q.filter_by.return_value.all.return_value = []
        elif model is ParticipantModel:

            def _p_filter(**kw: object) -> MagicMock:
                inner = MagicMock()
                inner.first.return_value = pmap.get(kw.get("id"))  # type: ignore[arg-type]
                return inner

            q.filter_by.side_effect = _p_filter
        elif model is ScoreEntryModel:

            def _se_filter(**kw: object) -> MagicMock:
                inner = MagicMock()
                if "song_id" in kw:
                    inner.first.return_value = None
                    inner.all.return_value = []
                elif "round_id" in kw:
                    inner.first.return_value = None
                    inner.all.return_value = _round_se
                elif "room_id" in kw:
                    inner.first.return_value = None
                    inner.all.return_value = _room_se
                else:
                    inner.first.return_value = None
                    inner.all.return_value = []
                return inner

            q.filter_by.side_effect = _se_filter
        return q

    mock.query.side_effect = _query
    return mock


def _make_round_of_10(
    round_id: UUID, room_id: UUID, current_index: int
) -> tuple[MagicMock, list[MagicMock]]:
    """Return (current_song, all_songs): current is LOCKED, previous are REVEALED."""
    songs = []
    for i in range(10):
        if i < current_index:
            status = SongStatus.REVEALED.value
        elif i == current_index:
            status = SongStatus.LOCKED.value
        else:
            status = SongStatus.UPCOMING.value
        songs.append(_song_mock(uuid4(), round_id, i, status))
    return songs[current_index], songs


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def host_token() -> str:
    return "next-song-host-token"


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def round_id() -> UUID:
    return uuid4()


# ── 1. passage chanson 1 → 2 après reveal ─────────────────────────────────────


def test_non_last_reveal_round_not_finished(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    """Révéler la chanson 1 (index 0) ne termine pas la manche."""
    current, all_songs = _make_round_of_10(round_id, room_id, 0)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    result = RoomService(sess).reveal_song(current.id, host_token)
    assert result["round_finished"] is False


def test_non_last_reveal_round_leaderboard_empty(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    """Pas de classement manche tant que la manche n'est pas terminée."""
    current, all_songs = _make_round_of_10(round_id, room_id, 0)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    result = RoomService(sess).reveal_song(current.id, host_token)
    assert result["round_leaderboard"] == []


# ── 2. progression index 1 → 10 ───────────────────────────────────────────────


@pytest.mark.parametrize("song_index", range(9))
def test_intermediate_reveals_do_not_finish_round(
    host_token: str, room_id: UUID, round_id: UUID, song_index: int
) -> None:
    """Révéler les chansons 0–8 ne termine pas la manche."""
    current, all_songs = _make_round_of_10(round_id, room_id, song_index)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    result = RoomService(sess).reveal_song(current.id, host_token)
    assert result["round_finished"] is False


# ── 3. fin après chanson 10 ────────────────────────────────────────────────────


def test_last_song_reveal_finishes_round(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    """Révéler la chanson 10 (index 9) termine la manche."""
    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    result = RoomService(sess).reveal_song(current.id, host_token)
    assert result["round_finished"] is True


def test_last_song_reveal_sets_round_status_finished(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    RoomService(sess).reveal_song(current.id, host_token)
    assert round_.status == RoundStatus.FINISHED.value


def test_last_song_reveal_sets_room_status_round_finished(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    RoomService(sess).reveal_song(current.id, host_token)
    assert room.status == RoomStatus.ROUND_FINISHED.value


# ── 4. refus chanson 11 ────────────────────────────────────────────────────────


def test_start_song_after_round_finished_raises(room_id: UUID, round_id: UUID) -> None:
    """Impossible de démarrer une chanson sur un round terminé."""
    round_ = _round_mock(round_id, room_id, status=RoundStatus.FINISHED.value)
    song = _song_mock(uuid4(), round_id, 0, SongStatus.UPCOMING.value)

    mock_session = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is SongModel:
            q.filter_by.return_value.first.return_value = song
        return q

    mock_session.query.side_effect = _query
    with pytest.raises(RoundNotInProgressError):
        RoomService(mock_session).start_song(round_id, 10)


# ── 5. classement manche calculé ──────────────────────────────────────────────


def test_round_leaderboard_on_last_reveal(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    """Le classement de manche contient les bons points par participant."""
    alice_id = uuid4()
    bob_id = uuid4()
    alice = _participant_mock(alice_id, "Alice")
    bob = _participant_mock(bob_id, "Bob")

    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)

    se_alice = _score_entry_mock(alice_id, room_id, round_id, current.id, 200)
    se_bob = _score_entry_mock(bob_id, room_id, round_id, current.id, 150)
    room_se = [se_alice, se_bob]
    round_se = [se_alice, se_bob]

    sess = _build_session(
        current,
        all_songs,
        round_,
        room,
        [alice, bob],
        room_score_entries=room_se,
        round_score_entries=round_se,
    )
    result = RoomService(sess).reveal_song(current.id, host_token)

    lb = result["round_leaderboard"]
    assert len(lb) == 2
    assert lb[0]["participant_id"] == alice_id
    assert lb[0]["round_points"] == 200
    assert lb[0]["rank"] == 1
    assert lb[1]["participant_id"] == bob_id
    assert lb[1]["round_points"] == 150
    assert lb[1]["rank"] == 2


def test_round_leaderboard_tie_same_rank(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    alice_id = uuid4()
    bob_id = uuid4()
    alice = _participant_mock(alice_id, "Alice")
    bob = _participant_mock(bob_id, "Bob")

    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)

    se_alice = _score_entry_mock(alice_id, room_id, round_id, current.id, 100)
    se_bob = _score_entry_mock(bob_id, room_id, round_id, current.id, 100)

    sess = _build_session(
        current,
        all_songs,
        round_,
        room,
        [alice, bob],
        room_score_entries=[se_alice, se_bob],
        round_score_entries=[se_alice, se_bob],
    )
    result = RoomService(sess).reveal_song(current.id, host_token)

    lb = result["round_leaderboard"]
    assert lb[0]["rank"] == lb[1]["rank"] == 1


def test_round_leaderboard_empty_when_no_scores(
    host_token: str, room_id: UUID, round_id: UUID
) -> None:
    current, all_songs = _make_round_of_10(round_id, room_id, 9)
    round_ = _round_mock(round_id, room_id)
    room = _room_mock(room_id, host_token)
    sess = _build_session(current, all_songs, round_, room, [])
    result = RoomService(sess).reveal_song(current.id, host_token)
    assert result["round_leaderboard"] == []
