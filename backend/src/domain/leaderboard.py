from dataclasses import dataclass
from uuid import UUID

from .entities import ScoreEntry


@dataclass(frozen=True)
class LeaderboardEntry:
    participant_id: UUID
    points: int
    rank: int


@dataclass(frozen=True)
class TeamLeaderboardEntry:
    team_id: UUID
    points: int
    rank: int


def compute_leaderboard(score_entries: list[ScoreEntry]) -> list[LeaderboardEntry]:
    totals: dict[UUID, int] = {}
    for entry in score_entries:
        pid = entry.participant_id
        totals[pid] = totals.get(pid, 0) + entry.points

    sorted_pairs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    result: list[LeaderboardEntry] = []
    for i, (participant_id, points) in enumerate(sorted_pairs):
        if i > 0 and points == sorted_pairs[i - 1][1]:
            rank = result[-1].rank
        else:
            rank = i + 1
        result.append(
            LeaderboardEntry(participant_id=participant_id, points=points, rank=rank)
        )
    return result


def compute_team_leaderboard(
    score_entries: list[ScoreEntry],
    participant_to_team: dict[UUID, UUID],
) -> list[TeamLeaderboardEntry]:
    totals: dict[UUID, int] = {}
    for entry in score_entries:
        team_id = participant_to_team.get(entry.participant_id)
        if team_id is not None:
            totals[team_id] = totals.get(team_id, 0) + entry.points

    sorted_pairs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    result: list[TeamLeaderboardEntry] = []
    for i, (team_id, points) in enumerate(sorted_pairs):
        if i > 0 and points == sorted_pairs[i - 1][1]:
            rank = result[-1].rank
        else:
            rank = i + 1
        result.append(TeamLeaderboardEntry(team_id=team_id, points=points, rank=rank))
    return result
