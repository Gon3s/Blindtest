"""Integration tests for T-015 MVP tables — require a running PostgreSQL.

Set TEST_DATABASE_URL env var or use the default.
"""

import os
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy.exc
from alembic.config import Config
from sqlalchemy import inspect, text

from alembic import command
from src.infrastructure.db import get_engine

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blindtest_test",
)
BACKEND_ROOT = Path(__file__).parent.parent.parent

EXPECTED_TABLES = {
    "rooms",
    "participants",
    "teams",
    "rounds",
    "songs",
    "answers",
    "score_entries",
    "room_events",
}

_ALL_TABLES = [
    "room_events",
    "score_entries",
    "answers",
    "songs",
    "rounds",
    "participants",
    "teams",
    "rooms",
    "alembic_version",
]


@pytest.fixture
def alembic_cfg() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg


@pytest.fixture
def migrated_engine(alembic_cfg: Config):  # type: ignore[return]
    eng = get_engine(TEST_DB_URL)
    with eng.connect() as conn:
        for table in _ALL_TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        conn.commit()
    command.upgrade(alembic_cfg, "head")
    yield eng
    command.downgrade(alembic_cfg, "base")
    eng.dispose()


def test_migration_creates_all_tables(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    insp = inspect(migrated_engine)
    tables = set(insp.get_table_names())
    assert EXPECTED_TABLES.issubset(tables)


def test_insert_room(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    room_id = uuid4()
    with migrated_engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO rooms (id, code, status, host_id, host_token, config)"
                " VALUES (:id, :code, :status, :host_id, :host_token,"
                        " CAST(:config AS JSONB))"
            ),
            {
                "id": str(room_id),
                "code": "ABCD1234",
                "status": "created",
                "host_id": str(uuid4()),
                "host_token": "test-host-token-abc",
                "config": "{}",
            },
        )
        conn.commit()
        result = conn.execute(
            text("SELECT code FROM rooms WHERE id = :id"), {"id": str(room_id)}
        )
        row = result.fetchone()
    assert row is not None
    assert row[0] == "ABCD1234"


def test_insert_participant(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    room_id = uuid4()
    participant_id = uuid4()
    with migrated_engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO rooms (id, code, status, host_id, host_token, config)"
                " VALUES (:id, :code, :status, :host_id, :host_token,"
                        " CAST(:config AS JSONB))"
            ),
            {
                "id": str(room_id),
                "code": "XYZW5678",
                "status": "created",
                "host_id": str(participant_id),
                "host_token": "test-host-token-xyz",
                "config": "{}",
            },
        )
        conn.execute(
            text(
                "INSERT INTO participants (id, nickname, room_id, is_host)"
                " VALUES (:id, :nickname, :room_id, :is_host)"
            ),
            {
                "id": str(participant_id),
                "nickname": "Alice",
                "room_id": str(room_id),
                "is_host": True,
            },
        )
        conn.commit()
        result = conn.execute(
            text("SELECT nickname FROM participants WHERE id = :id"),
            {"id": str(participant_id)},
        )
        row = result.fetchone()
    assert row is not None
    assert row[0] == "Alice"


def test_room_code_unique_constraint(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    with migrated_engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO rooms (id, code, status, host_id, host_token, config)"
                " VALUES (:id, :code, :status, :host_id, :host_token,"
                        " CAST(:config AS JSONB))"
            ),
            {
                "id": str(uuid4()),
                "code": "DUPL1234",
                "status": "created",
                "host_id": str(uuid4()),
                "host_token": "test-host-token-dup1",
                "config": "{}",
            },
        )
        conn.commit()

    with migrated_engine.connect() as conn:
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO rooms (id, code, status, host_id, host_token, config)"
                    " VALUES (:id, :code, :status, :host_id, :host_token,"
                        " CAST(:config AS JSONB))"
                ),
                {
                    "id": str(uuid4()),
                    "code": "DUPL1234",
                    "status": "created",
                    "host_id": str(uuid4()),
                    "host_token": "dup-host-token",
                    "config": "{}",
                },
            )
            conn.commit()


def test_participant_room_fk_constraint(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    with migrated_engine.connect() as conn:
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO participants (id, nickname, room_id, is_host)"
                    " VALUES (:id, :nickname, :room_id, :is_host)"
                ),
                {
                    "id": str(uuid4()),
                    "nickname": "Ghost",
                    "room_id": str(uuid4()),
                    "is_host": False,
                },
            )
            conn.commit()
