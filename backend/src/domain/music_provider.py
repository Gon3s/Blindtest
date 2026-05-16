from dataclasses import dataclass, field
from typing import Optional, Protocol
from uuid import UUID

from .entities import Song


@dataclass
class TrackInfo:
    title: str
    artist: str
    preview_url: Optional[str] = None
    aliases_title: list[str] = field(default_factory=list)
    aliases_artist: list[str] = field(default_factory=list)


class MusicProvider(Protocol):
    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]: ...


def track_to_song(track: TrackInfo, round_id: UUID, index: int) -> Song:
    return Song(
        title=track.title,
        artist=track.artist,
        round_id=round_id,
        index=index,
        preview_url=track.preview_url,
        aliases_title=list(track.aliases_title),
        aliases_artist=list(track.aliases_artist),
    )
