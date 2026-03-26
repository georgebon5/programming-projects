from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")


class CreateTenantAdminRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=255)
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    tenant_description: str | None = Field(default=None, max_length=1000)

    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in_seconds: int


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


# ── Two-Factor Authentication ────────────────────────────────────────────────

class TOTPCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TOTPSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str
