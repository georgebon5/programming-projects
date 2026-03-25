"""
User SQLAlchemy model.
Represents a user within a specific tenant.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserRole(str, enum.Enum):
    """User roles for tenant access control."""
    ADMIN = "admin"      # Full access: manage users, documents, settings
    MEMBER = "member"    # Can upload docs, run queries
    VIEWER = "viewer"    # Read-only access


class User(Base):
    """
    Represents a user within a tenant.

    WHY this design:
    - tenant_id as FK ensures strict tenant isolation (critical security)
    - Each user belongs to ONE tenant only (no multi-tenant access)
    - Role enum for RBAC (role-based access control)
    - email unique per tenant, not globally (allows email reuse across tenants)
    - last_login for tracking user activity
    """
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    email = Column(String(255), nullable=False, index=True)
    username = Column(String(150), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="uploaded_by_user", foreign_keys="Document.uploaded_by_id")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"
