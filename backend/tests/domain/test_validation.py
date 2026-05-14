from src.domain.enums import ValidationStatus
from src.domain.validation import ValidationResult, validate_answer


class TestValidationTicketExamples:
    """Acceptance criteria from T-012: One More Time — Daft Punk."""

    def test_title_exact_validates_title_only(self) -> None:
        result = validate_answer("one more time", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.FOUND
        assert result.artist == ValidationStatus.NOT_FOUND

    def test_artist_exact_validates_artist_only(self) -> None:
        result = validate_answer("daft punk", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.NOT_FOUND
        assert result.artist == ValidationStatus.FOUND

    def test_title_and_artist_combined_validates_both(self) -> None:
        result = validate_answer(
            "one more time daft punk", "One More Time", "Daft Punk"
        )
        assert result.title == ValidationStatus.FOUND
        assert result.artist == ValidationStatus.FOUND

    def test_title_typo_returns_found_or_doubtful(self) -> None:
        result = validate_answer("one more taime", "One More Time", "Daft Punk")
        assert result.title in (ValidationStatus.FOUND, ValidationStatus.DOUBTFUL)
        assert result.artist == ValidationStatus.NOT_FOUND

    def test_artist_typo_returns_found_or_doubtful(self) -> None:
        result = validate_answer("daft ponk", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.NOT_FOUND
        assert result.artist in (ValidationStatus.FOUND, ValidationStatus.DOUBTFUL)

    def test_unrelated_answer_returns_not_found(self) -> None:
        result = validate_answer("around the world", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.NOT_FOUND
        assert result.artist == ValidationStatus.NOT_FOUND


class TestValidationExactMatch:
    def test_exact_match_case_insensitive(self) -> None:
        result = validate_answer("ONE MORE TIME", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.FOUND

    def test_exact_match_with_accent(self) -> None:
        result = validate_answer("Céline Dion", "Céline Dion", "Some Song")
        assert result.title == ValidationStatus.FOUND

    def test_exact_match_with_punctuation(self) -> None:
        result = validate_answer("One More Time!", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.FOUND


class TestValidationAliases:
    def test_title_alias_returns_found(self) -> None:
        result = validate_answer(
            "omt",
            "One More Time",
            "Daft Punk",
            title_aliases=["omt"],
        )
        assert result.title == ValidationStatus.FOUND

    def test_artist_alias_returns_found(self) -> None:
        result = validate_answer(
            "dp",
            "One More Time",
            "Daft Punk",
            artist_aliases=["dp"],
        )
        assert result.artist == ValidationStatus.FOUND

    def test_title_alias_case_insensitive(self) -> None:
        result = validate_answer(
            "OMT",
            "One More Time",
            "Daft Punk",
            title_aliases=["omt"],
        )
        assert result.title == ValidationStatus.FOUND

    def test_no_alias_match_with_wrong_alias(self) -> None:
        result = validate_answer(
            "xyz",
            "One More Time",
            "Daft Punk",
            title_aliases=["omt"],
        )
        assert result.title == ValidationStatus.NOT_FOUND


class TestValidationFuzzy:
    def test_one_char_insertion_is_doubtful(self) -> None:
        result = validate_answer("one more taime", "One More Time", "Daft Punk")
        assert result.title != ValidationStatus.NOT_FOUND

    def test_one_char_substitution_is_doubtful(self) -> None:
        result = validate_answer("daft ponk", "One More Time", "Daft Punk")
        assert result.artist != ValidationStatus.NOT_FOUND

    def test_completely_wrong_is_not_found(self) -> None:
        result = validate_answer("hello world foo", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.NOT_FOUND
        assert result.artist == ValidationStatus.NOT_FOUND


class TestValidationResult:
    def test_result_is_dataclass_with_title_and_artist(self) -> None:
        result = ValidationResult(
            title=ValidationStatus.FOUND,
            artist=ValidationStatus.NOT_FOUND,
        )
        assert result.title == ValidationStatus.FOUND
        assert result.artist == ValidationStatus.NOT_FOUND

    def test_empty_answer_returns_not_found(self) -> None:
        result = validate_answer("", "One More Time", "Daft Punk")
        assert result.title == ValidationStatus.NOT_FOUND
        assert result.artist == ValidationStatus.NOT_FOUND
