"""
SQLAlchemy database configuration and session management.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings

# Create SQLAlchemy engine
kwargs = {
    "echo": settings.debug,  # Log SQL queries in development
}

# For SQLite, add special connection args (no pooling needed)
if settings.database_url.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}
    kwargs["poolclass"] = NullPool
else:
    # Production PostgreSQL: proper connection pooling
    kwargs["poolclass"] = QueuePool
    kwargs["pool_size"] = 10
    kwargs["max_overflow"] = 20
    kwargs["pool_pre_ping"] = True       # Verify connections before use
    kwargs["pool_recycle"] = 1800        # Recycle connections every 30 min

engine = create_engine(settings.database_url, **kwargs)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


def get_session_factory() -> sessionmaker:
    """Return the current session factory. Overridable for tests."""
    return SessionLocal


def get_db() -> Generator:
    """
    Dependency for getting database session.
    Usage in FastAPI routes: "db: Session = Depends(get_db)"
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    # Import models before create_all so SQLAlchemy metadata is populated.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
