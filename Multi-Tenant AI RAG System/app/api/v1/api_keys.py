"""
API key management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.api_key import APIKeyCreatedResponse, APIKeyResponse, CreateAPIKeyRequest
from app.services.api_key_service import APIKeyService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: CreateAPIKeyRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> APIKeyCreatedResponse:
    """Create a new API key. The raw key is returned only once."""
    svc = APIKeyService(db)
    key_obj, raw_key = svc.create_key(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=payload.name,
        expires_at=payload.expires_at,
    )

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.SETTINGS_UPDATE,
        resource_type="api_key",
        resource_id=str(key_obj.id),
        details={"name": payload.name},
    )

    data = APIKeyResponse.model_validate(key_obj).model_dump()
    data["raw_key"] = raw_key
    return APIKeyCreatedResponse(**data)


@router.get("/", response_model=list[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[APIKeyResponse]:
    svc = APIKeyService(db)
    keys = svc.list_keys(current_user.id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    svc = APIKeyService(db)
    key_obj = svc.revoke_key(key_id, current_user.id)
    if key_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.SETTINGS_UPDATE,
        resource_type="api_key",
        resource_id=str(key_id),
        details={"action": "revoke"},
    )


@router.post("/cleanup", tags=["API Keys"])
def cleanup_expired_keys(
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> dict:
    """Deactivate all expired API keys. Admin only."""
    svc = APIKeyService(db)
    count = svc.cleanup_expired_keys()
    return {"deactivated_count": count}
