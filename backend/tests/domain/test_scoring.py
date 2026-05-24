from src.domain.enums import AnswerMode
from src.domain.scoring import compute_song_score


class TestComputeSongScore:
    def test_nothing_found_gives_zero(self) -> None:
        assert compute_song_score(title_found=False, artist_found=False) == 0

    def test_title_only_gives_100(self) -> None:
        assert compute_song_score(title_found=True, artist_found=False) == 100

    def test_artist_only_gives_100(self) -> None:
        assert compute_song_score(title_found=False, artist_found=True) == 100

    def test_both_found_gives_250(self) -> None:
        # 100 title + 100 artist + 50 combo = 250
        assert compute_song_score(title_found=True, artist_found=True) == 250

    def test_both_found_full_speed_bonus_gives_300(self) -> None:
        assert (
            compute_song_score(
                title_found=True,
                artist_found=True,
                time_remaining_seconds=30.0,
                total_seconds=30.0,
            )
            == 300
        )

    def test_title_only_full_speed_bonus_gives_150(self) -> None:
        assert (
            compute_song_score(
                title_found=True,
                artist_found=False,
                time_remaining_seconds=30.0,
                total_seconds=30.0,
            )
            == 150
        )

    def test_artist_only_full_speed_bonus_gives_150(self) -> None:
        assert (
            compute_song_score(
                title_found=False,
                artist_found=True,
                time_remaining_seconds=30.0,
                total_seconds=30.0,
            )
            == 150
        )

    def test_both_found_half_speed_gives_275(self) -> None:
        # 250 + round(0.5 * 50) = 250 + 25 = 275
        assert (
            compute_song_score(
                title_found=True,
                artist_found=True,
                time_remaining_seconds=15.0,
                total_seconds=30.0,
            )
            == 275
        )

    def test_both_found_zero_time_remaining_gives_250(self) -> None:
        assert (
            compute_song_score(
                title_found=True,
                artist_found=True,
                time_remaining_seconds=0.0,
                total_seconds=30.0,
            )
            == 250
        )

    def test_nothing_found_no_speed_bonus_despite_time(self) -> None:
        assert (
            compute_song_score(
                title_found=False,
                artist_found=False,
                time_remaining_seconds=30.0,
                total_seconds=30.0,
            )
            == 0
        )

    def test_negative_time_remaining_treated_as_zero(self) -> None:
        assert (
            compute_song_score(
                title_found=True,
                artist_found=False,
                time_remaining_seconds=-5.0,
                total_seconds=30.0,
            )
            == 100
        )

    def test_maximum_never_exceeded(self) -> None:
        score = compute_song_score(
            title_found=True,
            artist_found=True,
            time_remaining_seconds=30.0,
            total_seconds=30.0,
        )
        assert score <= 300


class TestComputeSongScoreWithAnswerMode:
    def test_title_only_ignores_artist_found(self) -> None:
        # artist_found=True mais mode=TITLE_ONLY → 0 points artiste, 0 combo
        score = compute_song_score(True, True, answer_mode=AnswerMode.TITLE_ONLY)
        assert score == 100

    def test_title_only_no_score_when_title_not_found(self) -> None:
        score = compute_song_score(False, True, answer_mode=AnswerMode.TITLE_ONLY)
        assert score == 0

    def test_title_only_full_speed_bonus_gives_150(self) -> None:
        score = compute_song_score(
            True,
            True,
            time_remaining_seconds=30.0,
            total_seconds=30.0,
            answer_mode=AnswerMode.TITLE_ONLY,
        )
        assert score == 150

    def test_artist_only_ignores_title_found(self) -> None:
        score = compute_song_score(True, True, answer_mode=AnswerMode.ARTIST_ONLY)
        assert score == 100

    def test_artist_only_no_score_when_artist_not_found(self) -> None:
        score = compute_song_score(True, False, answer_mode=AnswerMode.ARTIST_ONLY)
        assert score == 0

    def test_artist_only_full_speed_bonus_gives_150(self) -> None:
        score = compute_song_score(
            True,
            True,
            time_remaining_seconds=30.0,
            total_seconds=30.0,
            answer_mode=AnswerMode.ARTIST_ONLY,
        )
        assert score == 150

    def test_both_mode_behavior_unchanged(self) -> None:
        score = compute_song_score(True, True, answer_mode=AnswerMode.BOTH)
        assert score == 250

    def test_default_mode_is_both(self) -> None:
        assert compute_song_score(True, True) == compute_song_score(
            True, True, answer_mode=AnswerMode.BOTH
        )
