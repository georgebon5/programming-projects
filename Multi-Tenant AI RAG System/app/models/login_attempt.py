"""
LoginAttempt model — persistent tracking of failed login attempts for account lockout.
Replaces the in-memory dict approach so lockout survives restarts and works with
multiple workers.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Uuid

from app.db.database import Base


class LoginAttempt(Base):
    """Tracks consecutive failed login attempts per email for account lockout."""

    __tablename__ = "login_attempts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    failed_count = Column(Integer, nullable=False, default=0)
    last_failed_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<LoginAttempt(email={self.email}, failed={self.failed_count})>"
