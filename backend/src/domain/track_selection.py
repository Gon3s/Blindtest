import random
import unicodedata

from .entities import RoomConfig
from .music_provider import MusicProvider, TrackInfo

_POOL_FACTOR: int = 3


def _normalize_key(title: str, artist: str) -> str:
    def _norm(s: str) -> str:
        s = s.lower().strip()
        s = unicodedata.normalize("NFD", s)
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

    return f"{_norm(title)}||{_norm(artist)}"


def select_round_tracks(
    theme: str,
    config: RoomConfig,
    primary_provider: MusicProvider,
    fallback_provider: MusicProvider,
    rng: random.Random | None = None,
) -> list[TrackInfo]:
    if rng is None:
        rng = random.Random()

    target = config.max_songs_per_round
    pool_size = target * _POOL_FACTOR

    raw = primary_provider.search(theme, limit=pool_size)
    valid = [t for t in raw if t.title.strip() and t.artist.strip()]

    seen: set[str] = set()
    deduped: list[TrackInfo] = []
    for track in valid:
        key = _normalize_key(track.title, track.artist)
        if key not in seen:
            seen.add(key)
            deduped.append(track)

    with_preview = [t for t in deduped if t.preview_url]
    without_preview = [t for t in deduped if not t.preview_url]
    rng.shuffle(with_preview)
    rng.shuffle(without_preview)
    candidates = with_preview + without_preview

    if len(candidates) < target:
        fallback_raw = fallback_provider.search(theme, limit=pool_size)
        fallback_valid = [
            t for t in fallback_raw if t.title.strip() and t.artist.strip()
        ]
        fallback_new: list[TrackInfo] = []
        for track in fallback_valid:
            key = _normalize_key(track.title, track.artist)
            if key not in seen:
                seen.add(key)
                fallback_new.append(track)
        rng.shuffle(fallback_new)
        candidates = candidates + fallback_new

    return candidates[:target]
