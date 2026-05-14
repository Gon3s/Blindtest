from uuid import uuid4

from src.domain.entities import ScoreEntry
from src.domain.leaderboard import (
    LeaderboardEntry,
    compute_leaderboard,
    compute_team_leaderboard,
)


def _entry(participant_id, points, *, room_id=None, song_id=None, round_id=None):
    return ScoreEntry(
        participant_id=participant_id,
        room_id=room_id or uuid4(),
        points=points,
        song_id=song_id,
        round_id=round_id,
    )


class TestComputeLeaderboard:
    def test_empty_returns_empty(self) -> None:
        assert compute_leaderboard([]) == []

    def test_single_participant_rank_one(self) -> None:
        p = uuid4()
        result = compute_leaderboard([_entry(p, 250)])
        assert result == [LeaderboardEntry(participant_id=p, points=250, rank=1)]

    def test_sorted_descending(self) -> None:
        p1, p2, p3 = uuid4(), uuid4(), uuid4()
        result = compute_leaderboard(
            [_entry(p1, 100), _entry(p2, 300), _entry(p3, 200)]
        )
        assert [e.participant_id for e in result] == [p2, p3, p1]

    def test_ranks_assigned_correctly(self) -> None:
        p1, p2, p3 = uuid4(), uuid4(), uuid4()
        result = compute_leaderboard(
            [_entry(p1, 100), _entry(p2, 300), _entry(p3, 200)]
        )
        assert [e.rank for e in result] == [1, 2, 3]

    def test_tie_shares_rank_competitive(self) -> None:
        p1, p2, p3 = uuid4(), uuid4(), uuid4()
        result = compute_leaderboard(
            [_entry(p1, 200), _entry(p2, 200), _entry(p3, 100)]
        )
        tied = [e for e in result if e.points == 200]
        assert all(e.rank == 1 for e in tied)
        last = next(e for e in result if e.points == 100)
        assert last.rank == 3

    def test_cumulates_multiple_entries_per_participant(self) -> None:
        p1, p2 = uuid4(), uuid4()
        room = uuid4()
        entries = [
            ScoreEntry(participant_id=p1, room_id=room, points=100),
            ScoreEntry(participant_id=p1, room_id=room, points=150),
            ScoreEntry(participant_id=p2, room_id=room, points=200),
        ]
        result = compute_leaderboard(entries)
        p1_entry = next(e for e in result if e.participant_id == p1)
        assert p1_entry.points == 250

    def test_round_leaderboard_cumulates_songs(self) -> None:
        p1, p2 = uuid4(), uuid4()
        room, round1 = uuid4(), uuid4()
        song1, song2 = uuid4(), uuid4()
        entries = [
            _entry(p1, 100, room_id=room, round_id=round1, song_id=song1),
            _entry(p1, 100, room_id=room, round_id=round1, song_id=song2),
            _entry(p2, 250, room_id=room, round_id=round1, song_id=song1),
        ]
        result = compute_leaderboard(entries)
        p1_entry = next(e for e in result if e.participant_id == p1)
        assert p1_entry.points == 200
        assert p1_entry.rank == 2

    def test_global_leaderboard_cumulates_across_rounds(self) -> None:
        p1, p2 = uuid4(), uuid4()
        room = uuid4()
        round1, round2 = uuid4(), uuid4()
        entries = [
            _entry(p1, 100, room_id=room, round_id=round1),
            _entry(p2, 150, room_id=room, round_id=round1),
            _entry(p1, 200, room_id=room, round_id=round2),
            _entry(p2, 50, room_id=room, round_id=round2),
        ]
        result = compute_leaderboard(entries)
        p1_entry = next(e for e in result if e.participant_id == p1)
        p2_entry = next(e for e in result if e.participant_id == p2)
        assert p1_entry.points == 300
        assert p1_entry.rank == 1
        assert p2_entry.points == 200
        assert p2_entry.rank == 2

    def test_all_tied_all_rank_one(self) -> None:
        p1, p2, p3 = uuid4(), uuid4(), uuid4()
        result = compute_leaderboard(
            [_entry(p1, 100), _entry(p2, 100), _entry(p3, 100)]
        )
        assert all(e.rank == 1 for e in result)


class TestComputeTeamLeaderboard:
    def test_empty_returns_empty(self) -> None:
        assert compute_team_leaderboard([], {}) == []

    def test_aggregates_team_scores(self) -> None:
        team1, team2 = uuid4(), uuid4()
        p1, p2, p3 = uuid4(), uuid4(), uuid4()
        room = uuid4()
        p_to_t = {p1: team1, p2: team1, p3: team2}
        entries = [
            ScoreEntry(participant_id=p1, room_id=room, points=100),
            ScoreEntry(participant_id=p2, room_id=room, points=150),
            ScoreEntry(participant_id=p3, room_id=room, points=200),
        ]
        result = compute_team_leaderboard(entries, p_to_t)
        t1 = next(e for e in result if e.team_id == team1)
        t2 = next(e for e in result if e.team_id == team2)
        assert t1.points == 250
        assert t2.points == 200

    def test_team_ranking_sorted_descending(self) -> None:
        team1, team2 = uuid4(), uuid4()
        p1, p2 = uuid4(), uuid4()
        room = uuid4()
        entries = [
            ScoreEntry(participant_id=p1, room_id=room, points=100),
            ScoreEntry(participant_id=p2, room_id=room, points=300),
        ]
        result = compute_team_leaderboard(entries, {p1: team1, p2: team2})
        assert result[0].team_id == team2
        assert result[0].rank == 1
        assert result[1].team_id == team1
        assert result[1].rank == 2

    def test_team_tie_shares_rank(self) -> None:
        team1, team2 = uuid4(), uuid4()
        p1, p2 = uuid4(), uuid4()
        room = uuid4()
        entries = [
            ScoreEntry(participant_id=p1, room_id=room, points=200),
            ScoreEntry(participant_id=p2, room_id=room, points=200),
        ]
        result = compute_team_leaderboard(entries, {p1: team1, p2: team2})
        assert all(e.rank == 1 for e in result)

    def test_participant_without_team_ignored(self) -> None:
        team1 = uuid4()
        p1, p2 = uuid4(), uuid4()
        room = uuid4()
        entries = [
            ScoreEntry(participant_id=p1, room_id=room, points=100),
            ScoreEntry(participant_id=p2, room_id=room, points=300),
        ]
        result = compute_team_leaderboard(entries, {p1: team1})
        assert len(result) == 1
        assert result[0].team_id == team1
