from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.room_service import RoomService
from src.domain.enums import SongStatus
from src.domain.exceptions import ParticipantNotInRoomError
from src.infrastructure.models import ParticipantModel, RoundModel, SongModel


def _make_playing_song() -> MagicMock:
    song = MagicMock(spec=SongModel)
    song.id = uuid4()
    song.round_id = uuid4()
    song.status = SongStatus.PLAYING.value
    song.title = "One More Time"
    song.artist = "Daft Punk"
    song.aliases_title = []
    song.aliases_artist = []
    return song


def _session_for_membership(
    song: MagicMock,
    room_id: UUID | None,
    participant_room_id: UUID | None,
) -> MagicMock:
    mock = MagicMock()

    round_ = MagicMock(spec=RoundModel)
    round_.id = song.round_id
    round_.room_id = room_id

    participant: MagicMock | None
    if participant_room_id is not None:
        participant = MagicMock(spec=ParticipantModel)
        participant.room_id = participant_room_id
    else:
        participant = None

    def _query(model: type) -> MagicMock:
        q = MagicMock()
        if model is SongModel:
            q.filter_by.return_value.first.return_value = song
        elif model is RoundModel:
            q.filter_by.return_value.first.return_value = round_
        elif model is ParticipantModel:
            q.filter_by.return_value.first.return_value = participant
        else:
            q.filter_by.return_value.first.return_value = None
        return q

    mock.query.side_effect = _query
    return mock


def test_submit_answer_correct_participant_accepted() -> None:
    room_id = uuid4()
    song = _make_playing_song()
    mock = _session_for_membership(song, room_id=room_id, participant_room_id=room_id)
    service = RoomService(mock)
    result = service.submit_answer(song.id, uuid4(), "Daft Punk")
    assert isinstance(result["answer_id"], UUID)


def test_submit_answer_unknown_participant_raises() -> None:
    room_id = uuid4()
    song = _make_playing_song()
    mock = _session_for_membership(song, room_id=room_id, participant_room_id=None)
    service = RoomService(mock)
    with pytest.raises(ParticipantNotInRoomError):
        service.submit_answer(song.id, uuid4(), "Daft Punk")


def test_submit_answer_participant_wrong_room_raises() -> None:
    room_id = uuid4()
    other_room_id = uuid4()
    song = _make_playing_song()
    mock = _session_for_membership(
        song, room_id=room_id, participant_room_id=other_room_id
    )
    service = RoomService(mock)
    with pytest.raises(ParticipantNotInRoomError):
        service.submit_answer(song.id, uuid4(), "Daft Punk")
