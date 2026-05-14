from uuid import uuid4

import pytest

from src.domain.entities import Song
from src.domain.enums import SongStatus
from src.domain.exceptions import SongTransitionError


def make_song(status: SongStatus = SongStatus.UPCOMING) -> Song:
    return Song(
        title="One More Time",
        artist="Daft Punk",
        round_id=uuid4(),
        index=0,
        status=status,
    )


class TestSongValidTransitions:
    def test_play_upcoming_to_playing(self) -> None:
        song = make_song(SongStatus.UPCOMING)
        song.play()
        assert song.status == SongStatus.PLAYING

    def test_lock_playing_to_locked(self) -> None:
        song = make_song(SongStatus.PLAYING)
        song.lock()
        assert song.status == SongStatus.LOCKED

    def test_validate_locked_to_validation(self) -> None:
        song = make_song(SongStatus.LOCKED)
        song.validate()
        assert song.status == SongStatus.VALIDATION

    def test_reveal_from_locked(self) -> None:
        song = make_song(SongStatus.LOCKED)
        song.reveal()
        assert song.status == SongStatus.REVEALED

    def test_reveal_from_validation(self) -> None:
        song = make_song(SongStatus.VALIDATION)
        song.reveal()
        assert song.status == SongStatus.REVEALED

    def test_score_revealed_to_scored(self) -> None:
        song = make_song(SongStatus.REVEALED)
        song.score()
        assert song.status == SongStatus.SCORED

    def test_full_lifecycle_with_validation(self) -> None:
        song = make_song()
        song.play()
        song.lock()
        song.validate()
        song.reveal()
        song.score()
        assert song.status == SongStatus.SCORED

    def test_full_lifecycle_without_validation(self) -> None:
        song = make_song()
        song.play()
        song.lock()
        song.reveal()
        song.score()
        assert song.status == SongStatus.SCORED


class TestSongInvalidTransitions:
    def test_upcoming_cannot_lock(self) -> None:
        song = make_song(SongStatus.UPCOMING)
        with pytest.raises(SongTransitionError):
            song.lock()

    def test_upcoming_cannot_reveal(self) -> None:
        song = make_song(SongStatus.UPCOMING)
        with pytest.raises(SongTransitionError):
            song.reveal()

    def test_upcoming_cannot_score(self) -> None:
        song = make_song(SongStatus.UPCOMING)
        with pytest.raises(SongTransitionError):
            song.score()

    def test_playing_cannot_play_again(self) -> None:
        song = make_song(SongStatus.PLAYING)
        with pytest.raises(SongTransitionError):
            song.play()

    def test_playing_cannot_reveal(self) -> None:
        song = make_song(SongStatus.PLAYING)
        with pytest.raises(SongTransitionError):
            song.reveal()

    def test_playing_cannot_score(self) -> None:
        song = make_song(SongStatus.PLAYING)
        with pytest.raises(SongTransitionError):
            song.score()

    def test_locked_cannot_play(self) -> None:
        song = make_song(SongStatus.LOCKED)
        with pytest.raises(SongTransitionError):
            song.play()

    def test_locked_cannot_score(self) -> None:
        song = make_song(SongStatus.LOCKED)
        with pytest.raises(SongTransitionError):
            song.score()

    def test_validation_cannot_play(self) -> None:
        song = make_song(SongStatus.VALIDATION)
        with pytest.raises(SongTransitionError):
            song.play()

    def test_validation_cannot_lock(self) -> None:
        song = make_song(SongStatus.VALIDATION)
        with pytest.raises(SongTransitionError):
            song.lock()

    def test_validation_cannot_score(self) -> None:
        song = make_song(SongStatus.VALIDATION)
        with pytest.raises(SongTransitionError):
            song.score()

    def test_revealed_cannot_play(self) -> None:
        song = make_song(SongStatus.REVEALED)
        with pytest.raises(SongTransitionError):
            song.play()

    def test_revealed_cannot_lock(self) -> None:
        song = make_song(SongStatus.REVEALED)
        with pytest.raises(SongTransitionError):
            song.lock()

    def test_scored_cannot_play(self) -> None:
        song = make_song(SongStatus.SCORED)
        with pytest.raises(SongTransitionError):
            song.play()

    def test_scored_cannot_lock(self) -> None:
        song = make_song(SongStatus.SCORED)
        with pytest.raises(SongTransitionError):
            song.lock()

    def test_scored_cannot_reveal(self) -> None:
        song = make_song(SongStatus.SCORED)
        with pytest.raises(SongTransitionError):
            song.reveal()

    def test_error_message_contains_states(self) -> None:
        song = make_song(SongStatus.UPCOMING)
        with pytest.raises(SongTransitionError, match="upcoming"):
            song.lock()


class TestSongFinalState:
    def test_scored_is_terminal(self) -> None:
        song = make_song(SongStatus.SCORED)
        assert song.status == SongStatus.SCORED

    def test_scored_cannot_return_to_playing(self) -> None:
        song = make_song(SongStatus.SCORED)
        with pytest.raises(SongTransitionError):
            song.play()
