"""SQLAlchemy engine and session factory.

This module introduces ORM infrastructure while keeping legacy psycopg2
utilities intact during the migration period.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def create_db_engine():
    url = _normalize_database_url(os.getenv("DATABASE_URL", "").strip())
    if not url:
        return None

    pool_min = int(os.getenv("DB_POOL_MIN", 5))
    pool_max = int(os.getenv("DB_POOL_MAX", 50))

    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=pool_min,
        max_overflow=max(0, pool_max - pool_min),
        pool_timeout=int(os.getenv("DB_POOL_ACQUIRE_TIMEOUT", 10)),
        pool_pre_ping=True,
        future=True,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=UTC",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 3,
        },
    )


engine = create_db_engine()
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True) if engine else None


def get_engine():
    return engine
