from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class CreateRoomRequest(BaseModel):
    host_nickname: str

    @field_validator("host_nickname")
    @classmethod
    def nickname_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("host_nickname must not be empty")
        return v


class CreateRoomResponse(BaseModel):
    room_id: UUID
    code: str
    host_id: UUID
    host_token: str


class JoinRoomRequest(BaseModel):
    nickname: str

    @field_validator("nickname")
    @classmethod
    def nickname_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("nickname must not be empty")
        return v


class JoinRoomResponse(BaseModel):
    room_id: UUID
    participant_id: UUID


class StartRoundRequest(BaseModel):
    theme: str
    host_token: str

    @field_validator("theme")
    @classmethod
    def theme_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("theme must not be empty")
        return v


class StartRoundResponse(BaseModel):
    round_id: UUID
    room_id: UUID
    song_count: int
    theme: str


class ParticipantStateItem(BaseModel):
    participant_id: UUID
    nickname: str
    is_host: bool


class CurrentSongState(BaseModel):
    song_id: UUID
    song_index: int
    round_id: UUID
    ends_at: Optional[str] = None
    preview_url: Optional[str] = None
    total_songs: int


class GetRoomStateResponse(BaseModel):
    room_id: UUID
    code: str
    status: str
    participants: list[ParticipantStateItem]
    current_song: Optional[CurrentSongState] = None
