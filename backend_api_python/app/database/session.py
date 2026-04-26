"""SQLAlchemy session helpers."""
from contextlib import contextmanager
from typing import Generator

from app.database.engine import SessionFactory


@contextmanager
def get_session() -> Generator:
    if SessionFactory is None:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_factory():
    return SessionFactory
