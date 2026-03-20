"""
User SQLAlchemy model.
Represents a user within a specific tenant.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(150), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="uploaded_by_user", foreign_keys="Document.uploaded_by_id")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"
