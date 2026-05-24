from .enums import AnswerMode

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
    answer_mode: AnswerMode = AnswerMode.BOTH,
) -> int:
    effective_title = title_found and answer_mode in (
        AnswerMode.BOTH,
        AnswerMode.TITLE_ONLY,
    )
    effective_artist = artist_found and answer_mode in (
        AnswerMode.BOTH,
        AnswerMode.ARTIST_ONLY,
    )

    base = 0
    if effective_title:
        base += _TITLE_POINTS
    if effective_artist:
        base += _ARTIST_POINTS
    if effective_title and effective_artist:
        base += _COMBO_POINTS

    if base > 0 and total_seconds > 0:
        ratio = max(0.0, min(1.0, time_remaining_seconds / total_seconds))
        speed_bonus = round(ratio * _MAX_SPEED_BONUS)
    else:
        speed_bonus = 0

    return min(base + speed_bonus, _MAX_SCORE)
