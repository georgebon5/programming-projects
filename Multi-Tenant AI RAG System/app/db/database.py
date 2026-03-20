"""
SQLAlchemy database configuration and session management.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from typing import Generator

from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # Disable connection pooling in development
    echo=settings.debug,  # Log SQL queries in development
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


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
    Base.metadata.create_all(bind=engine)
