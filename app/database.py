"""
Database engine and session management.

The FastAPI backend instances are stateless: none of them keep any
in-memory data between requests. Every request that needs data opens a
short-lived SQLAlchemy session against PostgreSQL and closes it again,
which is what makes it safe to run several identical backend instances
behind NGINX.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    The session is always closed in the `finally` block, even if the
    request raises, so connections are never leaked back to the pool
    in a bad state.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
