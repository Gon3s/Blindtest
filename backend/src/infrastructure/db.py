import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_engine(url: str | None = None) -> Engine:
    database_url = url or os.environ["DATABASE_URL"]
    return create_engine(database_url)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(url: str | None = None) -> None:
    global _engine, _SessionLocal
    _engine = get_engine(url)
    _SessionLocal = make_session_factory(_engine)


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
