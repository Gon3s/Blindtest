"""Integration tests for DB connection — require a running PostgreSQL.

Set TEST_DATABASE_URL env var or these tests are skipped.
Default: postgresql://postgres:postgres@localhost:5432/blindtest_test
"""

import os

import pytest
from sqlalchemy import text

from src.infrastructure.db import get_engine

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blindtest_test",
)


@pytest.fixture
def engine():  # type: ignore[return]
    eng = get_engine(TEST_DB_URL)
    yield eng
    eng.dispose()


def test_engine_connects(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1


def test_engine_returns_correct_dialect(engine) -> None:  # type: ignore[no-untyped-def]
    assert engine.dialect.name == "postgresql"
