from typing import Any
from unittest.mock import MagicMock

import httpx

from src.domain.music_provider import TrackInfo
from src.infrastructure.deezer_music_provider import DeezerMusicProvider
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider

_DEEZER_TRACK: dict[str, Any] = {
    "id": 3135556,
    "title": "Harder, Better, Faster, Stronger",
    "artist": {"id": 27, "name": "Daft Punk"},
    "preview": "https://cdns-preview-d.dzcdn.net/stream/preview.mp3",
}

_DEEZER_TRACK_NO_PREVIEW: dict[str, Any] = {
    "id": 999,
    "title": "Robot Rock",
    "artist": {"id": 27, "name": "Daft Punk"},
    "preview": "",
}


def _make_deezer_response(tracks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": tracks, "total": len(tracks)}


def _mock_client(json_body: dict[str, Any]) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = json_body
    mock_response.raise_for_status.return_value = None
    mock = MagicMock(spec=httpx.Client)
    mock.get.return_value = mock_response
    return mock


class TestDeezerTrackMapping:
    def test_maps_title(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(_DEEZER_TRACK)
        assert track.title == "Harder, Better, Faster, Stronger"

    def test_maps_artist_name_from_nested_field(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(_DEEZER_TRACK)
        assert track.artist == "Daft Punk"

    def test_maps_preview_url_when_present(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(_DEEZER_TRACK)
        assert track.preview_url == "https://cdns-preview-d.dzcdn.net/stream/preview.mp3"

    def test_preview_url_is_none_when_empty_string(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(_DEEZER_TRACK_NO_PREVIEW)
        assert track.preview_url is None

    def test_preview_url_is_none_when_field_absent(self) -> None:
        item: dict[str, Any] = {
            "id": 1,
            "title": "One More Time",
            "artist": {"name": "Daft Punk"},
        }
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(item)
        assert track.preview_url is None

    def test_returns_track_info_instance(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        track = provider._map_track(_DEEZER_TRACK)
        assert isinstance(track, TrackInfo)


class TestDeezerMusicProviderSearch:
    def test_search_returns_tracks_from_deezer(self) -> None:
        body = _make_deezer_response([_DEEZER_TRACK])
        provider = DeezerMusicProvider(client=_mock_client(body))
        results = provider.search("Electronic", limit=1)
        assert len(results) == 1
        assert results[0].title == "Harder, Better, Faster, Stronger"

    def test_search_calls_deezer_api_with_params(self) -> None:
        body = _make_deezer_response([_DEEZER_TRACK])
        mock = _mock_client(body)
        provider = DeezerMusicProvider(client=mock)
        provider.search("Electro", limit=5)
        mock.get.assert_called_once()
        call_kwargs = mock.get.call_args
        assert "search" in call_kwargs.args[0]
        params = call_kwargs.kwargs.get("params", {})
        assert params.get("q") == "Electro"
        assert params.get("limit") == 5

    def test_search_respects_limit(self) -> None:
        tracks = [
            {**_DEEZER_TRACK, "id": i, "title": f"Track {i}"}
            for i in range(10)
        ]
        body = _make_deezer_response(tracks)
        provider = DeezerMusicProvider(client=_mock_client(body))
        results = provider.search("Electro", limit=3)
        assert len(results) == 3

    def test_search_falls_back_on_connection_error(self) -> None:
        fallback = StaticFixtureMusicProvider()
        mock = MagicMock(spec=httpx.Client)
        mock.get.side_effect = httpx.ConnectError("unreachable")
        provider = DeezerMusicProvider(fallback=fallback, client=mock)
        results = provider.search("Pop 90s", limit=3)
        assert len(results) == 3
        assert all(isinstance(t, TrackInfo) for t in results)

    def test_search_falls_back_on_non_200_response(self) -> None:
        fallback = StaticFixtureMusicProvider()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )
        mock = MagicMock(spec=httpx.Client)
        mock.get.return_value = mock_response
        provider = DeezerMusicProvider(fallback=fallback, client=mock)
        results = provider.search("Pop 90s", limit=5)
        assert len(results) == 5
        assert all(isinstance(t, TrackInfo) for t in results)

    def test_search_falls_back_when_deezer_returns_empty(self) -> None:
        fallback = StaticFixtureMusicProvider()
        body = _make_deezer_response([])
        provider = DeezerMusicProvider(fallback=fallback, client=_mock_client(body))
        results = provider.search("Pop 90s", limit=5)
        assert len(results) == 5

    def test_search_falls_back_on_malformed_json(self) -> None:
        fallback = StaticFixtureMusicProvider()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("invalid json")
        mock = MagicMock(spec=httpx.Client)
        mock.get.return_value = mock_response
        provider = DeezerMusicProvider(fallback=fallback, client=mock)
        results = provider.search("Pop 90s", limit=5)
        assert len(results) == 5

    def test_implements_music_provider_protocol(self) -> None:
        provider = DeezerMusicProvider(client=_mock_client({"data": []}))
        assert callable(getattr(provider, "search", None))

    def test_custom_fallback_is_used(self) -> None:
        class CountingFallback:
            called: int = 0

            def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
                self.called += 1
                return []

        fallback = CountingFallback()
        mock = MagicMock(spec=httpx.Client)
        mock.get.side_effect = httpx.ConnectError("unreachable")
        provider = DeezerMusicProvider(fallback=fallback, client=mock)
        provider.search("Jazz", limit=5)
        assert fallback.called == 1
