"""TDD — reveal_song service method (T-032)."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import SongStatus
from src.domain.exceptions import (
    NotHostError,
    SongNotFoundError,
    SongNotRevealableError,
)
from src.infrastructure.models import (
    AnswerModel,
    ParticipantModel,
    RoomModel,
    RoundModel,
    ScoreEntryModel,
    SongModel,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _song(status: str = SongStatus.LOCKED.value) -> MagicMock:
    s = MagicMock(spec=SongModel)
    s.id = uuid4()
    s.round_id = uuid4()
    s.title = "One More Time"
    s.artist = "Daft Punk"
    s.status = status
    s.started_at = None
    s.ends_at = None
    return s


def _round(room_id: UUID | None = None) -> MagicMock:
    r = MagicMock(spec=RoundModel)
    r.id = uuid4()
    r.room_id = room_id or uuid4()
    return r


def _room(host_token: str, room_id: UUID | None = None) -> MagicMock:
    r = MagicMock(spec=RoomModel)
    r.id = room_id or uuid4()
    r.host_token = host_token
    return r


def _answer(
    song_id: UUID,
    participant_id: UUID,
    text: str = "one more time",
    title_found: bool = False,
    artist_found: bool = False,
) -> MagicMock:
    a = MagicMock(spec=AnswerModel)
    a.id = uuid4()
    a.song_id = song_id
    a.participant_id = participant_id
    a.text = text
    a.title_found = title_found
    a.artist_found = artist_found
    return a


def _participant(pid: UUID, nickname: str) -> MagicMock:
    p = MagicMock(spec=ParticipantModel)
    p.id = pid
    p.nickname = nickname
    return p


def _score_entry(
    participant_id: UUID, room_id: UUID, song_id: UUID, points: int
) -> MagicMock:
    se = MagicMock(spec=ScoreEntryModel)
    se.id = uuid4()
    se.participant_id = participant_id
    se.room_id = room_id
    se.song_id = song_id
    se.points = points
    return se


def _session(
    song: MagicMock,
    round_: MagicMock,
    room: MagicMock,
    answers: list[MagicMock],
    participants: list[MagicMock],
    song_score_entries: list[MagicMock] | None = None,
    room_score_entries: list[MagicMock] | None = None,
) -> MagicMock:
    pmap = {p.id: p for p in participants}
    song_se_map: dict[UUID, MagicMock] = {}
    for se in song_score_entries or []:
        song_se_map[se.participant_id] = se

    mock = MagicMock()

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is RoomModel:
            q.filter_by.return_value.first.return_value = room
        elif model is AnswerModel:
            q.filter_by.return_value.all.return_value = answers
        elif model is ParticipantModel:

            def _fb(**kw: object) -> MagicMock:
                inner = MagicMock()
                inner.first.return_value = pmap.get(kw.get("id"))  # type: ignore[arg-type]
                return inner

            q.filter_by.side_effect = _fb
        elif model is ScoreEntryModel:

            def _se_fb(**kw: object) -> MagicMock:
                inner = MagicMock()
                pid = kw.get("participant_id")
                sid = kw.get("song_id")
                rid = kw.get("room_id")
                if sid is not None:
                    # per-song lookup: filter_by(participant_id=..., song_id=...)
                    inner.first.return_value = song_se_map.get(pid)  # type: ignore[arg-type]
                    inner.all.return_value = []
                elif rid is not None:
                    # room-level lookup: filter_by(room_id=...)
                    inner.first.return_value = None
                    inner.all.return_value = room_score_entries or []
                else:
                    inner.first.return_value = None
                    inner.all.return_value = []
                return inner

            q.filter_by.side_effect = _se_fb
        return q

    mock.query.side_effect = _query
    return mock


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def host_token() -> str:
    return "reveal-host-token"


@pytest.fixture
def room_id() -> UUID:
    return uuid4()


@pytest.fixture
def locked_song() -> MagicMock:
    return _song(status=SongStatus.LOCKED.value)


# ── 1. reveal OK depuis LOCKED ────────────────────────────────────────────────


def test_reveal_ok_transitions_song_to_revealed(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    RoomService(sess).reveal_song(locked_song.id, host_token)
    assert locked_song.status == SongStatus.REVEALED.value


def test_reveal_ok_returns_title_and_artist(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["title"] == "One More Time"
    assert result["artist"] == "Daft Punk"


def test_reveal_ok_returns_song_id_and_room_id(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["song_id"] == locked_song.id
    assert result["room_id"] == room_id


# ── 2. reveal impossible avant locked ────────────────────────────────────────


def test_reveal_from_playing_raises_not_revealable(
    host_token: str, room_id: UUID
) -> None:
    song = _song(status=SongStatus.PLAYING.value)
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(song, round_, room, [], [])
    with pytest.raises(SongNotRevealableError):
        RoomService(sess).reveal_song(song.id, host_token)


def test_reveal_from_upcoming_raises_not_revealable(
    host_token: str, room_id: UUID
) -> None:
    song = _song(status=SongStatus.UPCOMING.value)
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(song, round_, room, [], [])
    with pytest.raises(SongNotRevealableError):
        RoomService(sess).reveal_song(song.id, host_token)


def test_reveal_from_already_revealed_raises_not_revealable(
    host_token: str, room_id: UUID
) -> None:
    song = _song(status=SongStatus.REVEALED.value)
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(song, round_, room, [], [])
    with pytest.raises(SongNotRevealableError):
        RoomService(sess).reveal_song(song.id, host_token)


def test_reveal_ok_from_validation_status(host_token: str, room_id: UUID) -> None:
    song = _song(status=SongStatus.VALIDATION.value)
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(song, round_, room, [], [])
    result = RoomService(sess).reveal_song(song.id, host_token)
    assert result["song_id"] == song.id
    assert song.status == SongStatus.REVEALED.value


# ── 3. résultat joueur retourné ───────────────────────────────────────────────


def test_reveal_player_result_contains_answer_text(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(locked_song.id, alice_id, text="one more time", title_found=True)
    se = _score_entry(alice_id, room_id, locked_song.id, 117)
    sess = _session(locked_song, round_, room, [ans], [alice], [se], [se])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert len(result["player_results"]) == 1
    pr = result["player_results"][0]
    assert pr["nickname"] == "Alice"
    assert pr["answer"] == "one more time"
    assert pr["title_found"] is True
    assert pr["artist_found"] is False


def test_reveal_player_result_contains_score(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(locked_song.id, alice_id, title_found=True)
    se = _score_entry(alice_id, room_id, locked_song.id, 117)
    sess = _session(locked_song, round_, room, [ans], [alice], [se], [se])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["player_results"][0]["score"] == 117


def test_reveal_player_result_score_zero_when_no_score_entry(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    ans = _answer(locked_song.id, alice_id)
    sess = _session(locked_song, round_, room, [ans], [alice], [], [])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["player_results"][0]["score"] == 0


# ── 4. mini-classement correct ────────────────────────────────────────────────


def test_reveal_mini_leaderboard_sorted_by_total_points_desc(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    bob_id = uuid4()
    alice = _participant(alice_id, "Alice")
    bob = _participant(bob_id, "Bob")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)

    se_alice = _score_entry(alice_id, room_id, locked_song.id, 117)
    se_bob = _score_entry(bob_id, room_id, locked_song.id, 267)
    sess = _session(locked_song, round_, room, [], [alice, bob], [], [se_alice, se_bob])

    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    lb = result["mini_leaderboard"]
    assert lb[0]["participant_id"] == bob_id
    assert lb[0]["rank"] == 1
    assert lb[0]["total_points"] == 267
    assert lb[1]["participant_id"] == alice_id
    assert lb[1]["rank"] == 2
    assert lb[1]["total_points"] == 117


def test_reveal_mini_leaderboard_tie_same_rank(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    bob_id = uuid4()
    alice = _participant(alice_id, "Alice")
    bob = _participant(bob_id, "Bob")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)

    se_alice = _score_entry(alice_id, room_id, locked_song.id, 100)
    se_bob = _score_entry(bob_id, room_id, locked_song.id, 100)
    sess = _session(locked_song, round_, room, [], [alice, bob], [], [se_alice, se_bob])

    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    lb = result["mini_leaderboard"]
    assert lb[0]["rank"] == lb[1]["rank"] == 1


def test_reveal_mini_leaderboard_contains_nickname(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    alice_id = uuid4()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    se = _score_entry(alice_id, room_id, locked_song.id, 100)
    sess = _session(locked_song, round_, room, [], [alice], [], [se])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["mini_leaderboard"][0]["nickname"] == "Alice"


def test_reveal_empty_player_results_when_no_answers(
    host_token: str, room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token=host_token, room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).reveal_song(locked_song.id, host_token)
    assert result["player_results"] == []
    assert result["mini_leaderboard"] == []


# ── erreurs ───────────────────────────────────────────────────────────────────


def test_reveal_song_not_found_raises() -> None:
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    with pytest.raises(SongNotFoundError):
        RoomService(mock).reveal_song(uuid4(), uuid4())


def test_reveal_not_host_raises(room_id: UUID) -> None:
    song = _song()
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token="correct-host-token", room_id=room_id)
    sess = _session(song, round_, room, [], [])
    with pytest.raises(NotHostError):
        RoomService(sess).reveal_song(song.id, "wrong-host-token")


# ── reveal_song_auto (T-122) ──────────────────────────────────────────────────


def test_reveal_song_auto_transitions_to_revealed(
    room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token="any-token", room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    RoomService(sess).reveal_song_auto(locked_song.id)
    assert locked_song.status == SongStatus.REVEALED.value


def test_reveal_song_auto_returns_title_and_artist(
    room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token="any-token", room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).reveal_song_auto(locked_song.id)
    assert result["title"] == "One More Time"
    assert result["artist"] == "Daft Punk"


def test_reveal_song_auto_skips_host_token_check(
    room_id: UUID, locked_song: MagicMock
) -> None:
    round_ = _round(room_id=room_id)
    locked_song.round_id = round_.id
    room = _room(host_token="secret-nobody-knows", room_id=room_id)
    sess = _session(locked_song, round_, room, [], [])
    result = RoomService(sess).reveal_song_auto(locked_song.id)
    assert result["title"] == "One More Time"


# ── auto-scoring (T-122) ──────────────────────────────────────────────────────


def test_reveal_auto_scores_found_answer_without_host_override(
    room_id: UUID,
) -> None:
    alice_id = uuid4()
    song = _song()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token="any-token", room_id=room_id)
    ans = _answer(song.id, alice_id, title_found=True)
    sess = _session(song, round_, room, [ans], [alice], [], [])

    RoomService(sess).reveal_song_auto(song.id)

    added = [call.args[0] for call in sess.add.call_args_list]
    score_entries = [a for a in added if isinstance(a, ScoreEntryModel)]
    assert len(score_entries) >= 1
    entry = next(e for e in score_entries if e.participant_id == alice_id)
    assert entry.points == 100  # title only, no speed bonus (started_at=None)


def test_reveal_auto_scoring_skips_existing_score_entry(
    room_id: UUID,
) -> None:
    alice_id = uuid4()
    song = _song()
    alice = _participant(alice_id, "Alice")
    round_ = _round(room_id=room_id)
    song.round_id = round_.id
    room = _room(host_token="any-token", room_id=room_id)
    ans = _answer(song.id, alice_id, title_found=True)
    existing_se = _score_entry(alice_id, room_id, song.id, 42)
    sess = _session(song, round_, room, [ans], [alice], [existing_se], [existing_se])

    RoomService(sess).reveal_song_auto(song.id)

    added = [call.args[0] for call in sess.add.call_args_list]
    new_score_entries = [a for a in added if isinstance(a, ScoreEntryModel)]
    assert len(new_score_entries) == 0
