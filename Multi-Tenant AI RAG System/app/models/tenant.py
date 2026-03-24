"""
Tenant SQLAlchemy model.
Represents a company/organization using the platform.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class Tenant(Base):
    """
    Represents a company/organization that uses the platform.
    Each tenant is completely isolated and cannot see other tenants' data.

    WHY this design:
    - Separate database table ensures clear separation of concerns
    - UUID for scale & distributed systems
    - slug for URL-friendly access (e.g., /api/tenants/acme-corp)
    - subscription_tier for future monetization
    - Cascade delete ensures data cleanup (GDPR compliance)
    """
    __tablename__ = "tenants"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(1000), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"
