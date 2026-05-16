from src.domain.music_provider import TrackInfo

_CATALOG: dict[str, list[TrackInfo]] = {
    "Pop 90s": [
        TrackInfo(
            title="...Baby One More Time",
            artist="Britney Spears",
            aliases_title=["Baby One More Time", "Baby One More Time (Britney Spears)"],
            aliases_artist=["Britney"],
        ),
        TrackInfo(
            title="Wannabe",
            artist="Spice Girls",
            aliases_title=["Wanna Be", "Spice Girls Wannabe"],
            aliases_artist=["The Spice Girls"],
        ),
        TrackInfo(
            title="Smells Like Teen Spirit",
            artist="Nirvana",
            aliases_title=["Teen Spirit"],
            aliases_artist=[],
            preview_url=None,
        ),
        TrackInfo(
            title="No Scrubs",
            artist="TLC",
            aliases_title=["No Scrub"],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Creep",
            artist="Radiohead",
            aliases_title=[],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Waterfalls",
            artist="TLC",
            aliases_title=[],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Losing My Religion",
            artist="R.E.M.",
            aliases_title=["Losing My Religion (R.E.M.)"],
            aliases_artist=["REM"],
        ),
        TrackInfo(
            title="One Week",
            artist="Barenaked Ladies",
            aliases_title=[],
            aliases_artist=["BNL"],
        ),
        TrackInfo(
            title="MMMBop",
            artist="Hanson",
            aliases_title=["Mmm Bop", "Mmmmbop"],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Iris",
            artist="Goo Goo Dolls",
            aliases_title=[],
            aliases_artist=["The Goo Goo Dolls"],
        ),
    ],
    "French": [
        TrackInfo(
            title="La Bohème",
            artist="Charles Aznavour",
            aliases_title=["Boheme"],
            aliases_artist=["Aznavour"],
        ),
        TrackInfo(
            title="Ne me quitte pas",
            artist="Jacques Brel",
            aliases_title=["Ne me quitte pas (Brel)", "If You Go Away"],
            aliases_artist=["Brel"],
        ),
        TrackInfo(
            title="Je t'aime... moi non plus",
            artist="Serge Gainsbourg",
            aliases_title=["Je t'aime moi non plus"],
            aliases_artist=["Gainsbourg"],
        ),
        TrackInfo(
            title="La Vie en rose",
            artist="Édith Piaf",
            aliases_title=["La vie en rose", "La Vie En Rose"],
            aliases_artist=["Piaf", "Edith Piaf"],
        ),
        TrackInfo(
            title="Voyage Voyage",
            artist="Desireless",
            aliases_title=["Voyage"],
            aliases_artist=[],
        ),
        TrackInfo(
            title="L'Aziza",
            artist="Daniel Balavoine",
            aliases_title=["Aziza", "L Aziza"],
            aliases_artist=["Balavoine"],
        ),
        TrackInfo(
            title="Alexandrie Alexandra",
            artist="Claude François",
            aliases_title=["Alexandrie", "Alexandria Alexandra"],
            aliases_artist=["Cloclo", "Claude Francois"],
        ),
        TrackInfo(
            title="Alors on danse",
            artist="Stromae",
            aliases_title=["Alors on Dance"],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Formidable",
            artist="Stromae",
            aliases_title=[],
            aliases_artist=[],
        ),
        TrackInfo(
            title="Papaoutai",
            artist="Stromae",
            aliases_title=["Papa ou t'ai", "Papa ou t'es"],
            aliases_artist=[],
        ),
    ],
}


def _all_tracks() -> list[TrackInfo]:
    seen: set[str] = set()
    result: list[TrackInfo] = []
    for tracks in _CATALOG.values():
        for t in tracks:
            key = f"{t.title}|{t.artist}"
            if key not in seen:
                seen.add(key)
                result.append(t)
    return result


class StaticFixtureMusicProvider:
    def search(self, theme: str, limit: int = 10) -> list[TrackInfo]:
        tracks = _CATALOG.get(theme) or _all_tracks()
        return tracks[:limit]
