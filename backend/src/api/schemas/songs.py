from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StartSongResponse(BaseModel):
    song_id: UUID
    round_id: UUID
    room_id: UUID
    song_index: int
    started_at: datetime
    ends_at: datetime
    preview_url: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    participant_id: UUID
    text: str = Field(min_length=1)


class SubmitAnswerResponse(BaseModel):
    answer_id: UUID
    submitted_at: datetime
    validation_status: str
    title_found: bool
    artist_found: bool


class AnswerSummaryItem(BaseModel):
    answer_id: UUID
    participant_id: UUID
    nickname: str
    text: str
    validation_status: str
    title_found: bool
    artist_found: bool


class SongSummaryResponse(BaseModel):
    song_id: UUID
    title: str
    artist: str
    total_answers: int
    doubtful_count: int
    answers: list[AnswerSummaryItem]


class SongSummaryRequest(BaseModel):
    host_token: str


class OverrideAnswerRequest(BaseModel):
    host_token: str
    title_accepted: bool
    artist_accepted: bool


class OverrideAnswerResponse(BaseModel):
    answer_id: UUID
    title_found: bool
    artist_found: bool
    validation_status: str
    score: int


class RevealSongRequest(BaseModel):
    host_token: str


class PlayerRevealItem(BaseModel):
    participant_id: UUID
    nickname: str
    answer: str
    title_found: bool
    artist_found: bool
    score: int


class MiniLeaderboardItem(BaseModel):
    rank: int
    participant_id: UUID
    nickname: str
    total_points: int


class RoundLeaderboardItem(BaseModel):
    rank: int
    participant_id: UUID
    nickname: str
    round_points: int


class RevealSongResponse(BaseModel):
    song_id: UUID
    room_id: UUID
    title: str
    artist: str
    player_results: list[PlayerRevealItem]
    mini_leaderboard: list[MiniLeaderboardItem]
    round_finished: bool = False
    round_leaderboard: list[RoundLeaderboardItem] = []
