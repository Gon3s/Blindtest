from src.domain.normalization import normalize


class TestNormalizeTicketExamples:
    """Exact test cases from T-011 acceptance criteria."""

    def test_one_more_time_removes_punctuation(self) -> None:
        assert normalize("One More Time!") == "one more time"

    def test_daft_punk_replaces_dash(self) -> None:
        assert normalize("Daft-Punk") == "daft punk"

    def test_celine_dion_removes_accent(self) -> None:
        assert normalize("Céline Dion") == "celine dion"

    def test_lamour_toujours_removes_contracted_article(self) -> None:
        assert normalize("L'Amour Toujours") == "amour toujours"


class TestNormalizeLowercasing:
    def test_all_caps(self) -> None:
        assert normalize("DAFT PUNK") == "daft punk"

    def test_mixed_case(self) -> None:
        assert normalize("MiXeD CaSe") == "mixed case"


class TestNormalizeAccents:
    def test_acute_accent(self) -> None:
        assert normalize("é") == "e"

    def test_grave_accent(self) -> None:
        assert normalize("è") == "e"

    def test_circumflex(self) -> None:
        assert normalize("ô") == "o"

    def test_umlaut(self) -> None:
        assert normalize("ü") == "u"

    def test_cedilla(self) -> None:
        assert normalize("ç") == "c"

    def test_multiple_accents(self) -> None:
        assert normalize("Éléphant") == "elephant"


class TestNormalizePunctuation:
    def test_exclamation_mark(self) -> None:
        assert normalize("hello!") == "hello"

    def test_question_mark(self) -> None:
        assert normalize("why?") == "why"

    def test_comma(self) -> None:
        assert normalize("hello, world") == "hello world"

    def test_period(self) -> None:
        assert normalize("Mr. Jones") == "mr jones"

    def test_parentheses(self) -> None:
        assert normalize("song (remix)") == "song remix"


class TestNormalizeApostrophesAndDashes:
    def test_apostrophe_contracted_article_lowercase(self) -> None:
        assert normalize("l'amour") == "amour"

    def test_apostrophe_contracted_article_uppercase(self) -> None:
        assert normalize("L'amour") == "amour"

    def test_dash_replaced_by_space(self) -> None:
        assert normalize("rock-n-roll") == "rock n roll"

    def test_apostrophe_in_middle_of_word(self) -> None:
        # "don't" → contracted article rule doesn't apply (multiple chars before ')
        # apostrophe removed → "dont"
        assert normalize("don't") == "dont"


class TestNormalizeSpaces:
    def test_multiple_spaces_reduced(self) -> None:
        assert normalize("one  more   time") == "one more time"

    def test_leading_trailing_spaces_stripped(self) -> None:
        assert normalize("  hello  ") == "hello"

    def test_empty_string(self) -> None:
        assert normalize("") == ""
