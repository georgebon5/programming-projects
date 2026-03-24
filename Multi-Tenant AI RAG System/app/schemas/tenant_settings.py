"""
Tenant settings schemas — quotas and feature flags.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TenantSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    max_users: int
    max_documents: int
    max_storage_mb: int
    max_chat_messages_per_day: int
    chat_enabled: bool
    file_upload_enabled: bool


class UpdateTenantSettingsRequest(BaseModel):
    max_users: Optional[int] = Field(None, ge=0, le=10000)
    max_documents: Optional[int] = Field(None, ge=0, le=100000)
    max_storage_mb: Optional[int] = Field(None, ge=0, le=100000)
    max_chat_messages_per_day: Optional[int] = Field(None, ge=0, le=100000)
    chat_enabled: Optional[bool] = None
    file_upload_enabled: Optional[bool] = None


class UsageLimitDetail(BaseModel):
    current: float
    limit: int


class FeatureFlags(BaseModel):
    chat_enabled: bool
    file_upload_enabled: bool


class UsageResponse(BaseModel):
    users: UsageLimitDetail
    documents: UsageLimitDetail
    storage_mb: UsageLimitDetail
    chat_messages_today: UsageLimitDetail
    features: FeatureFlags
