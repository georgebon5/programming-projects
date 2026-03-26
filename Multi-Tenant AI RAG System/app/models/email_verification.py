"""
EmailVerificationToken model — one-time tokens sent to users to confirm their email address.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Uuid

from app.db.database import Base


class EmailVerificationToken(Base):
    """One-time email verification token scoped to a user."""

    __tablename__ = "email_verification_tokens"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(user_id={self.user_id}, used={self.is_used})>"
