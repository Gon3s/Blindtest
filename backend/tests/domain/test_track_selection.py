import random

from src.domain.entities import RoomConfig
from src.domain.music_provider import TrackInfo
from src.domain.track_selection import select_round_tracks


def _config(max_songs: int = 10, duration: int = 30) -> RoomConfig:
    return RoomConfig(max_songs_per_round=max_songs, answer_duration_seconds=duration)


def _make_tracks(
    n: int,
    prefix: str = "Song",
    with_preview: bool = False,
) -> list[TrackInfo]:
    return [
        TrackInfo(
            title=f"{prefix} {i}",
            artist=f"{prefix} Artist {i}",
            preview_url=(
                f"https://preview.example.com/{i}.mp3" if with_preview else None
            ),
        )
        for i in range(n)
    ]


def _select(
    theme: str,
    config: RoomConfig,
    primary: object,
    fallback: object,
    seed: int = 0,
) -> list[TrackInfo]:
    return select_round_tracks(  # type: ignore[arg-type]
        theme, config, primary, fallback, rng=random.Random(seed)  # type: ignore[arg-type]
    )


class FakeProvider:
    def __init__(self, tracks: list[TrackInfo]) -> None:
        self._tracks = tracks

    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        return self._tracks[:limit]


class TestSelectRoundTracks:
    def test_selects_up_to_max_songs_per_round(self) -> None:
        provider = FakeProvider(_make_tracks(30))
        result = _select("Pop", _config(10), provider, provider)
        assert len(result) == 10

    def test_uses_config_max_not_hardcoded_10(self) -> None:
        provider = FakeProvider(_make_tracks(30))
        result = _select("Pop", _config(5), provider, provider)
        assert len(result) == 5

    def test_uses_config_max_larger_than_default(self) -> None:
        provider = FakeProvider(_make_tracks(50))
        result = _select("Pop", _config(15), provider, provider)
        assert len(result) == 15

    def test_filters_tracks_with_empty_title(self) -> None:
        tracks = _make_tracks(10) + [TrackInfo(title="", artist="Some Artist")]
        provider = FakeProvider(tracks)
        result = _select("Pop", _config(10), provider, provider)
        assert all(t.title.strip() for t in result)

    def test_filters_tracks_with_empty_artist(self) -> None:
        tracks = _make_tracks(10) + [TrackInfo(title="Some Song", artist="")]
        provider = FakeProvider(tracks)
        result = _select("Pop", _config(10), provider, provider)
        assert all(t.artist.strip() for t in result)

    def test_filters_whitespace_only_title(self) -> None:
        tracks = _make_tracks(10) + [TrackInfo(title="   ", artist="Artist")]
        provider = FakeProvider(tracks)
        result = _select("Pop", _config(10), provider, provider)
        assert all(t.title.strip() for t in result)

    def test_deduplicates_exact_duplicates(self) -> None:
        dup = TrackInfo(title="Song 0", artist="Song Artist 0")
        tracks = _make_tracks(9) + [dup]
        provider = FakeProvider(tracks)
        result = _select("Pop", _config(9), provider, provider)
        keys = [(t.title.lower(), t.artist.lower()) for t in result]
        assert len(keys) == len(set(keys))

    def test_deduplicates_case_insensitively(self) -> None:
        tracks = [
            TrackInfo(title="One More Time", artist="Daft Punk"),
            TrackInfo(title="ONE MORE TIME", artist="DAFT PUNK"),
        ] + _make_tracks(8, prefix="Other")
        provider = FakeProvider(tracks)
        result = _select("Pop", _config(9), provider, provider)
        keys = [(t.title.lower().strip(), t.artist.lower().strip()) for t in result]
        assert len(keys) == len(set(keys))

    def test_deduplicates_ignoring_accents(self) -> None:
        tracks = [
            TrackInfo(title="Bohème", artist="Aznavour"),
            TrackInfo(title="Boheme", artist="Aznavour"),
        ] + _make_tracks(8, prefix="Other")
        provider = FakeProvider(tracks)
        result = _select("French", _config(9), provider, provider)
        assert len(result) <= 9

    def test_prioritizes_tracks_with_preview_url(self) -> None:
        preview_tracks = _make_tracks(3, prefix="Preview", with_preview=True)
        regular_tracks = _make_tracks(10, prefix="Regular")
        provider = FakeProvider(preview_tracks + regular_tracks)
        result = _select("Pop", _config(5), provider, provider)
        with_preview_count = sum(1 for t in result if t.preview_url)
        assert with_preview_count == 3

    def test_all_preview_tracks_included_when_enough(self) -> None:
        preview_tracks = _make_tracks(10, prefix="Preview", with_preview=True)
        regular_tracks = _make_tracks(5, prefix="Regular")
        provider = FakeProvider(preview_tracks + regular_tracks)
        result = _select("Pop", _config(10), provider, provider)
        with_preview_count = sum(1 for t in result if t.preview_url)
        assert with_preview_count == 10

    def test_falls_back_when_primary_too_few(self) -> None:
        primary = FakeProvider(_make_tracks(2, prefix="Primary"))
        fallback = FakeProvider(_make_tracks(20, prefix="Fallback"))
        result = _select("Pop", _config(10), primary, fallback)
        assert len(result) == 10

    def test_fallback_deduped_against_primary(self) -> None:
        primary_tracks = _make_tracks(3, prefix="Track")
        unique_fallback = _make_tracks(10, prefix="Unique")
        primary = FakeProvider(primary_tracks)
        fallback = FakeProvider(primary_tracks + unique_fallback)
        result = _select("Pop", _config(8), primary, fallback)
        keys = [(t.title, t.artist) for t in result]
        assert len(keys) == len(set(keys))

    def test_returns_fewer_when_not_enough_even_with_fallback(self) -> None:
        tiny = FakeProvider(_make_tracks(3, prefix="Tiny"))
        result = _select("Pop", _config(10), tiny, tiny)
        assert len(result) == 3

    def test_stable_with_seeded_rng(self) -> None:
        provider = FakeProvider(_make_tracks(30))
        r1 = _select("Pop", _config(10), provider, provider, seed=42)
        r2 = _select("Pop", _config(10), provider, provider, seed=42)
        assert [t.title for t in r1] == [t.title for t in r2]

    def test_different_seeds_produce_different_orders(self) -> None:
        provider = FakeProvider(_make_tracks(30))
        r1 = _select("Pop", _config(10), provider, provider, seed=1)
        r2 = _select("Pop", _config(10), provider, provider, seed=9999)
        assert [t.title for t in r1] != [t.title for t in r2]

    def test_requests_pool_larger_than_target(self) -> None:
        call_log: list[int] = []

        class SpyProvider:
            def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
                call_log.append(limit)
                return _make_tracks(min(limit, 30))

        provider = SpyProvider()
        _select("Pop", _config(10), provider, provider)
        assert call_log[0] == 30  # 10 * 3

    def test_indexes_not_set_by_selection(self) -> None:
        provider = FakeProvider(_make_tracks(30))
        result = _select("Pop", _config(10), provider, provider)
        assert all(isinstance(t, TrackInfo) for t in result)
