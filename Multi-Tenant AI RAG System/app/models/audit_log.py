"""
AuditLog SQLAlchemy model — tracks user actions for security and compliance.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Uuid

from app.db.database import Base


class AuditAction(str, enum.Enum):
    """Categories of auditable actions."""
    # Auth
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"

    # Users
    USER_INVITE = "user_invite"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PASSWORD_CHANGE = "password_change"

    # Documents
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_PROCESS = "document_process"

    # Chat
    CHAT_QUERY = "chat_query"
    CHAT_DELETE = "chat_delete"

    # Account
    DATA_EXPORT = "data_export"
    ACCOUNT_DELETE = "account_delete"

    # Admin
    SETTINGS_UPDATE = "settings_update"


class AuditLog(Base):
    """
    Immutable log of user actions per tenant.
    Used for security monitoring, compliance, and debugging.
    """
    __tablename__ = "audit_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)  # "document", "user", etc.
    resource_id = Column(String(255), nullable=True)  # ID of affected resource
    details = Column(Text, nullable=True)  # JSON-encoded extra info
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
