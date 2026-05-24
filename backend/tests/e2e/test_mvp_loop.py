"""
E2E test — MVP critical loop.

Covers the full game sequence through the application layer:
  Create → Join → Play → Answer → Validate → Reveal → Leaderboard → Restart

No PostgreSQL required: uses SQLite in-memory.
No Deezer required: uses StaticFixtureMusicProvider.
No sleeps: lock_song() is called directly to simulate timer expiry.

Run with: uv run pytest tests/e2e/
Included automatically in: ./scripts/check.sh (via pytest testpaths = ["tests"])
"""

import textwrap
from collections.abc import Generator
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.application.room_service import RevealSongResult, RoomService
from src.infrastructure.models import SongModel as SongModelDB
from src.infrastructure.static_fixture_provider import StaticFixtureMusicProvider

# SQLite-compatible DDL — JSONB→TEXT, UUID→TEXT; ORM bind/result processors still work.
_SQLITE_DDL = textwrap.dedent("""\
    CREATE TABLE rooms (
        id          TEXT PRIMARY KEY,
        code        VARCHAR(16)  NOT NULL UNIQUE,
        status      VARCHAR(32)  NOT NULL,
        host_id     TEXT         NOT NULL,
        host_token  TEXT         NOT NULL,
        config      TEXT         NOT NULL
    );
    CREATE TABLE teams (
        id       TEXT PRIMARY KEY,
        name     VARCHAR(100) NOT NULL,
        room_id  TEXT         NOT NULL REFERENCES rooms(id)
    );
    CREATE TABLE participants (
        id        TEXT PRIMARY KEY,
        nickname  VARCHAR(100) NOT NULL,
        room_id   TEXT         NOT NULL REFERENCES rooms(id),
        team_id   TEXT,
        is_host   BOOLEAN      NOT NULL DEFAULT 0
    );
    CREATE TABLE rounds (
        id           TEXT PRIMARY KEY,
        room_id      TEXT         NOT NULL REFERENCES rooms(id),
        "index"      INTEGER      NOT NULL,
        theme        VARCHAR(200) NOT NULL,
        status       VARCHAR(32)  NOT NULL,
        answer_mode  VARCHAR(32)  NOT NULL DEFAULT 'both'
    );
    CREATE TABLE songs (
        id              TEXT PRIMARY KEY,
        title           VARCHAR(300) NOT NULL,
        artist          VARCHAR(300) NOT NULL,
        round_id        TEXT         NOT NULL REFERENCES rounds(id),
        "index"         INTEGER      NOT NULL,
        aliases_title   TEXT         NOT NULL,
        aliases_artist  TEXT         NOT NULL,
        preview_url     TEXT,
        status          VARCHAR(32)  NOT NULL,
        started_at      DATETIME,
        ends_at         DATETIME
    );
    CREATE TABLE answers (
        id                TEXT PRIMARY KEY,
        song_id           TEXT         NOT NULL REFERENCES songs(id),
        participant_id    TEXT         NOT NULL REFERENCES participants(id),
        text              TEXT         NOT NULL,
        submitted_at      DATETIME     NOT NULL,
        title_found       BOOLEAN      NOT NULL DEFAULT 0,
        artist_found      BOOLEAN      NOT NULL DEFAULT 0,
        validation_status VARCHAR(32)  NOT NULL,
        host_override     VARCHAR(32)
    );
    CREATE TABLE score_entries (
        id              TEXT PRIMARY KEY,
        participant_id  TEXT     NOT NULL REFERENCES participants(id),
        room_id         TEXT     NOT NULL REFERENCES rooms(id),
        song_id         TEXT,
        round_id        TEXT,
        points          INTEGER  NOT NULL
    );
    CREATE TABLE room_events (
        id          TEXT PRIMARY KEY,
        room_id     TEXT         NOT NULL REFERENCES rooms(id),
        event_type  VARCHAR(100) NOT NULL,
        payload     TEXT         NOT NULL,
        created_at  DATETIME     NOT NULL
    );
""")

_MUSIC = StaticFixtureMusicProvider()


@pytest.fixture()
def svc() -> Generator[RoomService, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        for stmt in _SQLITE_DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()

    session = Session(engine)
    try:
        yield RoomService(session)
    finally:
        session.close()
        engine.dispose()


def test_mvp_loop(svc: RoomService) -> None:
    """Full MVP game loop: one song with host validation, then finish round."""

    # ── 1. Create room ──────────────────────────────────────────────────────
    room = svc.create_room("Alice")
    svc._session.commit()

    room_id: UUID = room["room_id"]
    host_token: str = room["host_token"]
    code: str = room["code"]
    assert len(code) == 6

    # ── 2. Join with a player ───────────────────────────────────────────────
    join = svc.join_room(code, "Bob")
    svc._session.commit()
    player_id: UUID = join["participant_id"]

    # ── 3. Start round — 10 songs from fixture, no Deezer ──────────────────
    round_result = svc.start_round(room_id, host_token, "Pop 90s", _MUSIC)
    svc._session.commit()
    round_id: UUID = round_result["round_id"]
    assert round_result["song_count"] == 10
    assert round_result["theme"] == "Pop 90s"

    # ── 4. Start song 0 ─────────────────────────────────────────────────────
    song0 = svc.start_song(round_id, 0)
    svc._session.commit()
    song_id: UUID = song0["song_id"]
    assert song0["song_index"] == 0
    assert song0["ends_at"] > song0["started_at"]

    # Look up actual song title (shuffle may reorder from fixture default)
    song0_model = svc._session.query(SongModelDB).filter_by(id=song_id).first()
    assert song0_model is not None
    song0_title: str = song0_model.title

    # ── 5. Bob submits a correct answer ─────────────────────────────────────
    answer = svc.submit_answer(song_id, player_id, song0_title)
    svc._session.commit()
    assert answer["title_found"] is True

    # ── 6. Timer expires: lock the song ──────────────────────────────────────
    svc.lock_song(song_id)
    svc._session.commit()

    # ── 7. Host reviews and confirms Bob's answer ───────────────────────────
    summary = svc.get_song_summary(song_id, host_token)
    assert summary["total_answers"] == 1
    assert summary["answers"][0]["title_found"] is True

    svc.override_answer(
        song_id,
        summary["answers"][0]["answer_id"],
        host_token,
        title_accepted=True,
        artist_accepted=True,
    )
    svc._session.commit()

    # ── 8. Reveal song — mini-leaderboard shows Bob's points ────────────────
    reveal = svc.reveal_song(song_id, host_token)
    svc._session.commit()

    assert reveal["title"] == song0_title
    assert len(reveal["player_results"]) == 1
    assert reveal["player_results"][0]["title_found"] is True
    assert reveal["player_results"][0]["score"] > 0
    assert len(reveal["mini_leaderboard"]) == 1
    assert reveal["mini_leaderboard"][0]["nickname"] == "Bob"
    assert reveal["mini_leaderboard"][0]["total_points"] > 0
    assert reveal["round_finished"] is False

    # ── 9. Cycle songs 1-9 to finish the round ──────────────────────────────
    final: RevealSongResult | None = None
    for idx in range(1, 10):
        s = svc.start_song(round_id, idx)
        svc._session.commit()
        svc.lock_song(s["song_id"])
        svc._session.commit()
        final = svc.reveal_song(s["song_id"], host_token)
        svc._session.commit()
        if final["round_finished"]:
            break

    assert final is not None
    assert final["round_finished"] is True
    assert len(final["round_leaderboard"]) == 1
    assert final["round_leaderboard"][0]["nickname"] == "Bob"
    assert final["round_leaderboard"][0]["round_points"] > 0

    # ── 10. Restart with a different theme ──────────────────────────────────
    restart = svc.restart_round(room_id, host_token, "French", _MUSIC)
    svc._session.commit()
    assert restart["song_count"] == 10
    assert restart["theme"] == "French"


def test_mvp_auto_reveal_scores_found_answer(svc: RoomService) -> None:
    """Auto-reveal (T-122): found answer scored without host override_answer call."""
    room = svc.create_room("Alice")
    svc._session.commit()
    room_id: UUID = room["room_id"]
    host_token: str = room["host_token"]
    code: str = room["code"]

    join = svc.join_room(code, "Bob")
    svc._session.commit()
    player_id: UUID = join["participant_id"]

    round_result = svc.start_round(room_id, host_token, "Pop 90s", _MUSIC)
    svc._session.commit()
    round_id: UUID = round_result["round_id"]

    song0 = svc.start_song(round_id, 0)
    svc._session.commit()
    song_id: UUID = song0["song_id"]

    song0_model = svc._session.query(SongModelDB).filter_by(id=song_id).first()
    assert song0_model is not None
    song0_title: str = song0_model.title

    answer = svc.submit_answer(song_id, player_id, song0_title)
    svc._session.commit()
    assert answer["title_found"] is True

    svc.lock_song(song_id)
    svc._session.commit()

    reveal = svc.reveal_song_auto(song_id)
    svc._session.commit()

    assert len(reveal["player_results"]) == 1
    assert reveal["player_results"][0]["score"] > 0
    assert len(reveal["mini_leaderboard"]) == 1
    assert reveal["mini_leaderboard"][0]["total_points"] > 0
