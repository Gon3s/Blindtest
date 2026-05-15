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
