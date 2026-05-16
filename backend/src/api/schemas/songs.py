from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StartSongResponse(BaseModel):
    song_id: UUID
    round_id: UUID
    room_id: UUID
    song_index: int
    started_at: datetime
    ends_at: datetime
