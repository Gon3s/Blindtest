from datetime import datetime
from uuid import uuid4

from src.domain.entities import (
    Answer,
    Participant,
    Room,
    Round,
    ScoreEntry,
    Song,
    Team,
)
from src.domain.enums import RoomStatus, RoundStatus, SongStatus, ValidationStatus


class TestRoom:
    def test_room_creation(self) -> None:
        host_id = uuid4()
        room = Room(host_id=host_id)
        assert room.host_id == host_id
        assert room.id is not None

    def test_room_default_status_is_created(self) -> None:
        room = Room(host_id=uuid4())
        assert room.status == RoomStatus.CREATED

    def test_room_default_config(self) -> None:
        room = Room(host_id=uuid4())
        assert room.config.max_songs_per_round == 10
        assert room.config.answer_duration_seconds == 30

    def test_room_default_collections_empty(self) -> None:
        room = Room(host_id=uuid4())
        assert room.participant_ids == []
        assert room.team_ids == []
        assert room.round_ids == []

    def test_room_code_default_empty(self) -> None:
        room = Room(host_id=uuid4())
        assert room.code == ""

    def test_room_status_can_transition_to_waiting(self) -> None:
        room = Room(host_id=uuid4())
        room.status = RoomStatus.WAITING
        assert room.status == RoomStatus.WAITING

    def test_room_status_can_transition_to_round_in_progress(self) -> None:
        room = Room(host_id=uuid4())
        room.status = RoomStatus.ROUND_IN_PROGRESS
        assert room.status == RoomStatus.ROUND_IN_PROGRESS

    def test_two_rooms_have_distinct_ids(self) -> None:
        r1 = Room(host_id=uuid4())
        r2 = Room(host_id=uuid4())
        assert r1.id != r2.id


class TestParticipant:
    def test_participant_creation(self) -> None:
        room_id = uuid4()
        p = Participant(nickname="Alice", room_id=room_id)
        assert p.nickname == "Alice"
        assert p.room_id == room_id
        assert p.id is not None

    def test_participant_default_not_host(self) -> None:
        p = Participant(nickname="Alice", room_id=uuid4())
        assert p.is_host is False

    def test_participant_default_no_team(self) -> None:
        p = Participant(nickname="Alice", room_id=uuid4())
        assert p.team_id is None

    def test_participant_can_be_host(self) -> None:
        p = Participant(nickname="Host", room_id=uuid4(), is_host=True)
        assert p.is_host is True

    def test_participant_can_have_team(self) -> None:
        team_id = uuid4()
        p = Participant(nickname="Alice", room_id=uuid4(), team_id=team_id)
        assert p.team_id == team_id

    def test_two_participants_have_distinct_ids(self) -> None:
        room_id = uuid4()
        p1 = Participant(nickname="Alice", room_id=room_id)
        p2 = Participant(nickname="Bob", room_id=room_id)
        assert p1.id != p2.id


class TestTeam:
    def test_team_creation(self) -> None:
        room_id = uuid4()
        team = Team(name="Blue Team", room_id=room_id)
        assert team.name == "Blue Team"
        assert team.room_id == room_id
        assert team.id is not None

    def test_team_default_no_members(self) -> None:
        team = Team(name="Blue Team", room_id=uuid4())
        assert team.member_ids == []

    def test_team_with_members(self) -> None:
        member_ids = [uuid4(), uuid4()]
        team = Team(name="Red Team", room_id=uuid4(), member_ids=member_ids)
        assert len(team.member_ids) == 2

    def test_two_teams_have_distinct_ids(self) -> None:
        room_id = uuid4()
        t1 = Team(name="Blue", room_id=room_id)
        t2 = Team(name="Red", room_id=room_id)
        assert t1.id != t2.id


class TestRound:
    def test_round_creation(self) -> None:
        room_id = uuid4()
        r = Round(room_id=room_id, index=1, theme="Pop 2000s")
        assert r.room_id == room_id
        assert r.index == 1
        assert r.theme == "Pop 2000s"
        assert r.id is not None

    def test_round_default_status_is_pending(self) -> None:
        r = Round(room_id=uuid4(), index=1, theme="Rock")
        assert r.status == RoundStatus.PENDING

    def test_round_default_no_songs(self) -> None:
        r = Round(room_id=uuid4(), index=1, theme="Rock")
        assert r.song_ids == []

    def test_round_status_can_transition_to_in_progress(self) -> None:
        r = Round(room_id=uuid4(), index=1, theme="Jazz")
        r.status = RoundStatus.IN_PROGRESS
        assert r.status == RoundStatus.IN_PROGRESS

    def test_round_index_two(self) -> None:
        room_id = uuid4()
        r = Round(room_id=room_id, index=2, theme="Electro")
        assert r.index == 2


class TestSong:
    def test_song_creation(self) -> None:
        round_id = uuid4()
        s = Song(title="One More Time", artist="Daft Punk", round_id=round_id, index=1)
        assert s.title == "One More Time"
        assert s.artist == "Daft Punk"
        assert s.round_id == round_id
        assert s.index == 1
        assert s.id is not None

    def test_song_default_status_is_upcoming(self) -> None:
        s = Song(
            title="Around the World", artist="Daft Punk", round_id=uuid4(), index=2
        )
        assert s.status == SongStatus.UPCOMING

    def test_song_default_no_preview(self) -> None:
        s = Song(title="Harder Better", artist="Daft Punk", round_id=uuid4(), index=3)
        assert s.preview_url is None

    def test_song_default_empty_aliases(self) -> None:
        s = Song(title="Get Lucky", artist="Daft Punk", round_id=uuid4(), index=4)
        assert s.aliases_title == []
        assert s.aliases_artist == []

    def test_song_with_aliases(self) -> None:
        s = Song(
            title="One More Time",
            artist="Daft Punk",
            round_id=uuid4(),
            index=1,
            aliases_title=["1 More Time"],
            aliases_artist=["DP"],
        )
        assert "1 More Time" in s.aliases_title
        assert "DP" in s.aliases_artist

    def test_song_default_no_timer(self) -> None:
        s = Song(title="Lose Yourself", artist="Eminem", round_id=uuid4(), index=5)
        assert s.started_at is None
        assert s.ends_at is None

    def test_song_status_can_transition_to_playing(self) -> None:
        s = Song(title="One More Time", artist="Daft Punk", round_id=uuid4(), index=1)
        s.status = SongStatus.PLAYING
        assert s.status == SongStatus.PLAYING

    def test_song_status_can_transition_to_locked(self) -> None:
        s = Song(title="One More Time", artist="Daft Punk", round_id=uuid4(), index=1)
        s.status = SongStatus.LOCKED
        assert s.status == SongStatus.LOCKED

    def test_song_index_ten(self) -> None:
        s = Song(title="Last Song", artist="Artist", round_id=uuid4(), index=10)
        assert s.index == 10

    def test_two_songs_have_distinct_ids(self) -> None:
        round_id = uuid4()
        s1 = Song(title="Song A", artist="Artist", round_id=round_id, index=1)
        s2 = Song(title="Song B", artist="Artist", round_id=round_id, index=2)
        assert s1.id != s2.id


class TestAnswer:
    def test_answer_creation(self) -> None:
        song_id = uuid4()
        participant_id = uuid4()
        now = datetime.now()
        a = Answer(
            song_id=song_id,
            participant_id=participant_id,
            text="One More Time",
            submitted_at=now,
        )
        assert a.song_id == song_id
        assert a.participant_id == participant_id
        assert a.text == "One More Time"
        assert a.submitted_at == now
        assert a.id is not None

    def test_answer_default_status_not_found(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="blah",
            submitted_at=datetime.now(),
        )
        assert a.validation_status == ValidationStatus.NOT_FOUND

    def test_answer_default_title_and_artist_not_found(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="blah",
            submitted_at=datetime.now(),
        )
        assert a.title_found is False
        assert a.artist_found is False

    def test_answer_default_no_host_override(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="blah",
            submitted_at=datetime.now(),
        )
        assert a.host_override is None

    def test_answer_with_title_found(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="One More Time",
            submitted_at=datetime.now(),
            title_found=True,
            validation_status=ValidationStatus.FOUND,
        )
        assert a.title_found is True
        assert a.validation_status == ValidationStatus.FOUND

    def test_answer_can_be_doubtful(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="one more taime",
            submitted_at=datetime.now(),
            validation_status=ValidationStatus.DOUBTFUL,
        )
        assert a.validation_status == ValidationStatus.DOUBTFUL

    def test_answer_host_override(self) -> None:
        a = Answer(
            song_id=uuid4(),
            participant_id=uuid4(),
            text="daft ponk",
            submitted_at=datetime.now(),
            validation_status=ValidationStatus.DOUBTFUL,
            host_override=ValidationStatus.FOUND,
        )
        assert a.host_override == ValidationStatus.FOUND


class TestScoreEntry:
    def test_score_entry_creation(self) -> None:
        participant_id = uuid4()
        room_id = uuid4()
        se = ScoreEntry(participant_id=participant_id, room_id=room_id, points=150)
        assert se.participant_id == participant_id
        assert se.room_id == room_id
        assert se.points == 150
        assert se.id is not None

    def test_score_entry_default_no_song_or_round(self) -> None:
        se = ScoreEntry(participant_id=uuid4(), room_id=uuid4(), points=0)
        assert se.song_id is None
        assert se.round_id is None

    def test_score_entry_with_song_id(self) -> None:
        song_id = uuid4()
        se = ScoreEntry(
            participant_id=uuid4(), room_id=uuid4(), points=100, song_id=song_id
        )
        assert se.song_id == song_id

    def test_score_entry_with_round_id(self) -> None:
        round_id = uuid4()
        se = ScoreEntry(
            participant_id=uuid4(), room_id=uuid4(), points=250, round_id=round_id
        )
        assert se.round_id == round_id

    def test_score_entry_zero_points(self) -> None:
        se = ScoreEntry(participant_id=uuid4(), room_id=uuid4(), points=0)
        assert se.points == 0

    def test_score_entry_max_points(self) -> None:
        se = ScoreEntry(participant_id=uuid4(), room_id=uuid4(), points=300)
        assert se.points == 300

    def test_two_score_entries_have_distinct_ids(self) -> None:
        participant_id = uuid4()
        room_id = uuid4()
        se1 = ScoreEntry(participant_id=participant_id, room_id=room_id, points=100)
        se2 = ScoreEntry(participant_id=participant_id, room_id=room_id, points=200)
        assert se1.id != se2.id
