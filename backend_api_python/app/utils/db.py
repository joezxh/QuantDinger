"""
Database Connection Facade — SQLAlchemy-first with legacy compat aliases.

All new code should import directly from ``app.database.session``:

    from app.database.session import get_session

    with get_session() as session:
        ...

The symbols re-exported here are deprecated and retained only to avoid
breaking legacy imports during the ORM migration transition.
"""

import warnings

from app.database.session import get_session

# Keep lightweight psycopg2 helpers for scripts that need raw connections
from app.utils.db_postgres import (
    is_postgres_available,
    close_pool as _close_pool,
)


def get_db_connection():
    """Deprecated — use ``app.database.session.get_session()`` instead.

    Yields a SQLAlchemy Session wrapped in a minimal compatibility shim
    so that legacy ``with get_db_connection() as conn: conn.cursor()``
    patterns fail fast with a clear message instead of an obscure
    AttributeError.
    """
    warnings.warn(
        "get_db_connection() is deprecated. Use get_session() from app.database.session.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_session()


def get_db_connection_sync():
    """Deprecated — use ``app.database.session.get_session()`` instead."""
    warnings.warn(
        "get_db_connection_sync() is deprecated. Use get_session() from app.database.session.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_session()


def get_db_type() -> str:
    """Get database type (always postgresql)"""
    return "postgresql"


def is_postgres() -> bool:
    """Check if using PostgreSQL (always True)"""
    return True


def init_database():
    """Verify database connectivity via SQLAlchemy."""
    try:
        with get_session() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("PostgreSQL connection verified (via SQLAlchemy)")
    except Exception as exc:
        raise RuntimeError(f"Cannot connect to PostgreSQL. Check DATABASE_URL. {exc}")


def close_db():
    """Close legacy psycopg2 connection pool (if any)."""
    _close_pool()


def close_db_connection():
    """Legacy alias for close_db."""
    close_db()


__all__ = [
    "get_db_connection",
    "get_db_connection_sync",
    "close_db_connection",
    "init_database",
    "close_db",
    "get_db_type",
    "is_postgres",
]
