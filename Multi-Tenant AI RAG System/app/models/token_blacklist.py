"""
BlacklistedToken SQLAlchemy model.
Stores invalidated JWT JTIs to prevent reuse after logout or rotation.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Uuid

from app.db.database import Base


class BlacklistedToken(Base):
    """
    Stores JTIs (JWT IDs) of tokens that have been explicitly revoked.

    WHY this design:
    - jti is the canonical identifier for a specific JWT
    - expires_at allows periodic cleanup of stale rows (tokens past their natural expiry)
    - Indexed jti ensures O(log n) lookups on every authenticated request
    """

    __tablename__ = "blacklisted_tokens"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    token_type = Column(String(16), nullable=False)  # "access" or "refresh"
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blacklisted_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_blacklisted_tokens_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<BlacklistedToken(jti={self.jti}, type={self.token_type}, user_id={self.user_id})>"
