from uuid import uuid4

from src.domain.entities import Song
from src.domain.music_provider import MusicProvider, TrackInfo, track_to_song
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider


class FakeMusicProvider:
    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        return [
            TrackInfo(
                title=f"Song {i}",
                artist=f"Artist {i}",
                preview_url=f"https://preview.example.com/{i}.mp3",
            )
            for i in range(limit)
        ]


def _is_music_provider(provider: MusicProvider) -> bool:
    return callable(getattr(provider, "search", None))


class TestMusicProviderProtocol:
    def test_fake_provider_implements_protocol(self) -> None:
        provider: MusicProvider = FakeMusicProvider()
        assert _is_music_provider(provider)

    def test_search_returns_list_of_track_info(self) -> None:
        provider = FakeMusicProvider()
        results = provider.search("Pop 90s", limit=3)
        assert len(results) == 3
        assert all(isinstance(t, TrackInfo) for t in results)

    def test_search_respects_limit(self) -> None:
        provider = FakeMusicProvider()
        assert len(provider.search("Rock", limit=5)) == 5
        assert len(provider.search("Jazz", limit=1)) == 1

    def test_search_with_default_limit(self) -> None:
        provider = FakeMusicProvider()
        results = provider.search("Electro")
        assert len(results) == 10

    def test_search_returns_track_with_expected_fields(self) -> None:
        provider = FakeMusicProvider()
        track = provider.search("Pop", limit=1)[0]
        assert track.title == "Song 0"
        assert track.artist == "Artist 0"
        assert track.preview_url == "https://preview.example.com/0.mp3"

    def test_search_different_themes_return_results(self) -> None:
        provider = FakeMusicProvider()
        pop = provider.search("Pop", limit=2)
        rock = provider.search("Rock", limit=2)
        assert len(pop) == 2
        assert len(rock) == 2


class TestTrackInfo:
    def test_track_info_minimal(self) -> None:
        track = TrackInfo(title="One More Time", artist="Daft Punk")
        assert track.title == "One More Time"
        assert track.artist == "Daft Punk"
        assert track.preview_url is None

    def test_track_info_with_preview_url(self) -> None:
        track = TrackInfo(
            title="Get Lucky",
            artist="Daft Punk",
            preview_url="https://cdn.deezer.com/preview/123.mp3",
        )
        assert track.preview_url == "https://cdn.deezer.com/preview/123.mp3"

    def test_track_info_aliases_default_empty(self) -> None:
        track = TrackInfo(title="Song", artist="Artist")
        assert track.aliases_title == []
        assert track.aliases_artist == []

    def test_track_info_cover_url_default_none(self) -> None:
        track = TrackInfo(title="Song", artist="Artist")
        assert track.cover_url is None

    def test_track_info_with_cover_url(self) -> None:
        track = TrackInfo(
            title="Song",
            artist="Artist",
            cover_url="https://cdn.deezer.com/images/cover.jpg",
        )
        assert track.cover_url == "https://cdn.deezer.com/images/cover.jpg"

    def test_track_info_with_aliases(self) -> None:
        track = TrackInfo(
            title="One More Time",
            artist="Daft Punk",
            aliases_title=["1 More Time"],
            aliases_artist=["DP"],
        )
        assert "1 More Time" in track.aliases_title
        assert "DP" in track.aliases_artist


class TestTrackToSong:
    def test_mapping_sets_title_and_artist(self) -> None:
        track = TrackInfo(title="One More Time", artist="Daft Punk")
        song = track_to_song(track, round_id=uuid4(), index=1)
        assert song.title == "One More Time"
        assert song.artist == "Daft Punk"

    def test_mapping_sets_round_id_and_index(self) -> None:
        round_id = uuid4()
        track = TrackInfo(title="Harder Better Faster", artist="Daft Punk")
        song = track_to_song(track, round_id=round_id, index=3)
        assert song.round_id == round_id
        assert song.index == 3

    def test_mapping_sets_preview_url(self) -> None:
        track = TrackInfo(
            title="Around the World",
            artist="Daft Punk",
            preview_url="https://cdn.deezer.com/preview/456.mp3",
        )
        song = track_to_song(track, round_id=uuid4(), index=2)
        assert song.preview_url == "https://cdn.deezer.com/preview/456.mp3"

    def test_mapping_preview_url_none_when_absent(self) -> None:
        track = TrackInfo(title="Robot Rock", artist="Daft Punk")
        song = track_to_song(track, round_id=uuid4(), index=4)
        assert song.preview_url is None

    def test_mapping_propagates_aliases(self) -> None:
        track = TrackInfo(
            title="One More Time",
            artist="Daft Punk",
            aliases_title=["1 More Time"],
            aliases_artist=["DP"],
        )
        song = track_to_song(track, round_id=uuid4(), index=1)
        assert song.aliases_title == ["1 More Time"]
        assert song.aliases_artist == ["DP"]

    def test_mapping_propagates_cover_url(self) -> None:
        track = TrackInfo(
            title="Song",
            artist="Artist",
            cover_url="https://cdn.deezer.com/images/cover.jpg",
        )
        song = track_to_song(track, round_id=uuid4(), index=0)
        assert song.cover_url == "https://cdn.deezer.com/images/cover.jpg"

    def test_mapping_cover_url_none_when_absent(self) -> None:
        track = TrackInfo(title="Song", artist="Artist")
        song = track_to_song(track, round_id=uuid4(), index=0)
        assert song.cover_url is None

    def test_mapping_returns_song_instance(self) -> None:
        track = TrackInfo(title="Instant Crush", artist="Daft Punk")
        result = track_to_song(track, round_id=uuid4(), index=5)
        assert isinstance(result, Song)

    def test_mapping_song_has_unique_id(self) -> None:
        track = TrackInfo(title="Lose Yourself to Dance", artist="Daft Punk")
        round_id = uuid4()
        s1 = track_to_song(track, round_id=round_id, index=1)
        s2 = track_to_song(track, round_id=round_id, index=1)
        assert s1.id != s2.id


class TestStaticFixtureMusicProvider:
    def test_search_by_known_theme_returns_tracks(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Pop 90s")
        assert len(results) > 0

    def test_search_returns_ten_songs_for_theme(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Pop 90s")
        assert len(results) >= 10

    def test_search_with_limit_respects_limit(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Pop 90s", limit=5)
        assert len(results) == 5

    def test_all_tracks_have_title_and_artist(self) -> None:
        provider = StaticFixtureMusicProvider()
        for track in provider.search("Pop 90s"):
            assert track.title
            assert track.artist

    def test_tracks_have_aliases(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Pop 90s")
        tracks_with_aliases = [
            t for t in results if t.aliases_title or t.aliases_artist
        ]
        assert len(tracks_with_aliases) > 0

    def test_unknown_theme_returns_fallback_tracks(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Unknown Theme XYZ")
        assert len(results) > 0

    def test_unknown_theme_fallback_respects_limit(self) -> None:
        provider = StaticFixtureMusicProvider()
        results = provider.search("Unknown Theme XYZ", limit=3)
        assert len(results) == 3

    def test_implements_music_provider_protocol(self) -> None:
        provider: MusicProvider = StaticFixtureMusicProvider()
        assert callable(getattr(provider, "search", None))
