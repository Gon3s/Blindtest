from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StartSongResponse(BaseModel):
    song_id: UUID
    round_id: UUID
    room_id: UUID
    song_index: int
    started_at: datetime
    ends_at: datetime


class SubmitAnswerRequest(BaseModel):
    participant_id: UUID
    text: str = Field(min_length=1)


class SubmitAnswerResponse(BaseModel):
    answer_id: UUID
    submitted_at: datetime
    validation_status: str
    title_found: bool
    artist_found: bool
