"""
Schemas for API key endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Returned only on creation — includes the full key (shown once)."""
    raw_key: str
