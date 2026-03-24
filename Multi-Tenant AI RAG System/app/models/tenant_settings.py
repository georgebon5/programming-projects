"""
TenantSettings SQLAlchemy model — configurable quotas and settings per tenant.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Uuid

from app.db.database import Base


class TenantSettings(Base):
    """
    Per-tenant configurable settings and quota limits.
    One row per tenant — created on tenant registration.
    """
    __tablename__ = "tenant_settings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Quota limits
    max_users = Column(Integer, default=10, nullable=False)
    max_documents = Column(Integer, default=100, nullable=False)
    max_storage_mb = Column(Integer, default=500, nullable=False)
    max_chat_messages_per_day = Column(Integer, default=200, nullable=False)

    # Feature flags
    chat_enabled = Column(Boolean, default=True, nullable=False)
    file_upload_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<TenantSettings(tenant_id={self.tenant_id})>"
