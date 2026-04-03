"""
Pydantic schemas for webhook endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_EVENTS = [
    "document.uploaded",
    "document.processed",
    "document.failed",
    "document.deleted",
    "user.invited",
    "user.deleted",
    "subscription.changed",
]


class WebhookCreate(BaseModel):
    url: str = Field(max_length=2048)
    events: list[str] = Field(min_length=1)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("events must not be empty")
        return v


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    events: list[str]
    is_active: bool
    description: str | None
    created_at: datetime


class WebhookListResponse(BaseModel):
    webhooks: list[WebhookResponse]
    total: int


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    response_status: int | None
    attempt_count: int
    delivered_at: datetime | None
    created_at: datetime
