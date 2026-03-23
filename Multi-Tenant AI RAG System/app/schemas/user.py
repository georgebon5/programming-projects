from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


# --- Requests ---

class InviteUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.MEMBER


class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=150)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# --- Responses ---

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
