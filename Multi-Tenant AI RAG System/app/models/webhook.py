"""
Webhook SQLAlchemy models — endpoint registration and delivery history.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.types import JSON as GenericJSON

from app.db.database import Base


class WebhookEndpoint(Base):
    """A registered webhook URL for a tenant."""

    __tablename__ = "webhook_endpoints"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url = Column(String(2048), nullable=False)
    secret = Column(String(255), nullable=False)  # HMAC signing key
    events = Column(GenericJSON, nullable=False)  # ["document.processed", ...]
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    description = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<WebhookEndpoint(id={self.id}, url={self.url})>"


class WebhookDelivery(Base):
    """Record of a single webhook delivery attempt."""

    __tablename__ = "webhook_deliveries"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    webhook_id = Column(
        Uuid,
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(100), nullable=False)
    payload = Column(GenericJSON, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, event={self.event_type}, status={self.response_status})>"
