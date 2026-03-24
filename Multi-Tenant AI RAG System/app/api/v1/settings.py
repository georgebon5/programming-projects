"""
Tenant Settings API — manage quotas, view usage (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.tenant_settings import (
    TenantSettingsResponse,
    UpdateTenantSettingsRequest,
    UsageResponse,
)
from app.services.tenant_settings_service import TenantSettingsService

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


@router.get("/", response_model=TenantSettingsResponse)
def get_settings(
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> TenantSettingsResponse:
    """Get tenant settings and quotas."""
    service = TenantSettingsService(db)
    settings = service.get_or_create(current_user.tenant_id)
    return TenantSettingsResponse.model_validate(settings)


@router.patch("/", response_model=TenantSettingsResponse)
def update_settings(
    payload: UpdateTenantSettingsRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> TenantSettingsResponse:
    """Update tenant settings and quotas."""
    service = TenantSettingsService(db)
    settings = service.update(
        current_user.tenant_id,
        **payload.model_dump(exclude_unset=True),
    )
    return TenantSettingsResponse.model_validate(settings)


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsageResponse:
    """Get current resource usage vs. limits. Available to all authenticated users."""
    service = TenantSettingsService(db)
    usage = service.get_usage(current_user.tenant_id)
    return UsageResponse(**usage)
