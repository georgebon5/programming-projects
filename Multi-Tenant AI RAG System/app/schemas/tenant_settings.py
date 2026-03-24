"""
Tenant settings schemas — quotas and feature flags.
"""


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
    max_users: int | None = Field(None, ge=0, le=10000)
    max_documents: int | None = Field(None, ge=0, le=100000)
    max_storage_mb: int | None = Field(None, ge=0, le=100000)
    max_chat_messages_per_day: int | None = Field(None, ge=0, le=100000)
    chat_enabled: bool | None = None
    file_upload_enabled: bool | None = None


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
