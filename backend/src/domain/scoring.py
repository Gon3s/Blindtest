_TITLE_POINTS = 100
_ARTIST_POINTS = 100
_COMBO_POINTS = 50
_MAX_SPEED_BONUS = 50
_MAX_SCORE = 300


def compute_song_score(
    title_found: bool,
    artist_found: bool,
    time_remaining_seconds: float = 0.0,
    total_seconds: float = 30.0,
) -> int:
    base = 0
    if title_found:
        base += _TITLE_POINTS
    if artist_found:
        base += _ARTIST_POINTS
    if title_found and artist_found:
        base += _COMBO_POINTS

    if base > 0 and total_seconds > 0:
        ratio = max(0.0, min(1.0, time_remaining_seconds / total_seconds))
        speed_bonus = round(ratio * _MAX_SPEED_BONUS)
    else:
        speed_bonus = 0

    return min(base + speed_bonus, _MAX_SCORE)
