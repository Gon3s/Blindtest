"""Integration tests for Alembic migrations — require a running PostgreSQL.

Runs migrations against blindtest_test, verifies alembic_version table exists,
then rolls back to base so the test DB stays clean.
"""

import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect, text

from alembic import command
from src.infrastructure.db import get_engine

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blindtest_test",
)

BACKEND_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def alembic_cfg() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg


@pytest.fixture
def migrated_engine(alembic_cfg: Config):  # type: ignore[return]
    eng = get_engine(TEST_DB_URL)
    # Ensure clean state before running
    with eng.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()
    command.upgrade(alembic_cfg, "head")
    yield eng
    command.downgrade(alembic_cfg, "base")
    eng.dispose()


def test_migration_creates_alembic_version_table(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    insp = inspect(migrated_engine)
    assert "alembic_version" in insp.get_table_names()


def test_migration_head_is_applied(migrated_engine) -> None:  # type: ignore[no-untyped-def]
    with migrated_engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0][0] is not None
