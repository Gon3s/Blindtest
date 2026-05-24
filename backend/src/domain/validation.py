from dataclasses import dataclass
from difflib import SequenceMatcher

from .enums import AnswerMode, ValidationStatus
from .normalization import normalize

_FUZZY_THRESHOLD = 0.75


@dataclass
class ValidationResult:
    title: ValidationStatus
    artist: ValidationStatus


def _match(answer_norm: str, target: str, aliases: list[str]) -> ValidationStatus:
    target_norm = normalize(target)
    aliases_norm = [normalize(a) for a in aliases]

    if answer_norm == target_norm or answer_norm in aliases_norm:
        return ValidationStatus.FOUND

    # Handles combined "title artist" answers
    if target_norm and target_norm in answer_norm:
        return ValidationStatus.FOUND

    best_ratio = SequenceMatcher(None, answer_norm, target_norm).ratio()
    for alias_norm in aliases_norm:
        alias_ratio = SequenceMatcher(None, answer_norm, alias_norm).ratio()
        best_ratio = max(best_ratio, alias_ratio)

    if best_ratio >= _FUZZY_THRESHOLD:
        return ValidationStatus.DOUBTFUL

    return ValidationStatus.NOT_FOUND


def validate_answer(
    answer: str,
    title: str,
    artist: str,
    title_aliases: list[str] | None = None,
    artist_aliases: list[str] | None = None,
    answer_mode: AnswerMode = AnswerMode.BOTH,
) -> ValidationResult:
    answer_norm = normalize(answer)
    title_result = (
        _match(answer_norm, title, title_aliases or [])
        if answer_mode in (AnswerMode.BOTH, AnswerMode.TITLE_ONLY)
        else ValidationStatus.NOT_FOUND
    )
    artist_result = (
        _match(answer_norm, artist, artist_aliases or [])
        if answer_mode in (AnswerMode.BOTH, AnswerMode.ARTIST_ONLY)
        else ValidationStatus.NOT_FOUND
    )
    return ValidationResult(title=title_result, artist=artist_result)
