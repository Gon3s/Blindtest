from typing import Any

import httpx

from src.domain.music_provider import MusicProvider, TrackInfo
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider

_DEEZER_SEARCH_URL = "https://api.deezer.com/search"


class DeezerMusicProvider:
    def __init__(
        self,
        fallback: MusicProvider | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._fallback: MusicProvider = fallback or StaticFixtureMusicProvider()
        self._client = client or httpx.Client(timeout=5.0)

    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        try:
            response = self._client.get(
                _DEEZER_SEARCH_URL,
                params={"q": theme, "limit": limit},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            items: list[dict[str, Any]] = data.get("data", [])[:limit]
            tracks = [self._map_track(item) for item in items]
            if not tracks:
                return self._fallback.search(theme, limit)
            return tracks
        except Exception:
            return self._fallback.search(theme, limit)

    @staticmethod
    def _map_track(item: dict[str, Any]) -> TrackInfo:
        raw_preview: str = item.get("preview", "") or ""
        album: dict[str, Any] = item.get("album") or {}
        raw_cover: str = album.get("cover_medium") or ""
        title: str = item["title"]
        title_short: str = item.get("title_short", "") or ""
        aliases_title = [title_short] if title_short and title_short != title else []
        return TrackInfo(
            title=title,
            artist=item["artist"]["name"],
            preview_url=raw_preview if raw_preview else None,
            cover_url=raw_cover if raw_cover else None,
            aliases_title=aliases_title,
        )
