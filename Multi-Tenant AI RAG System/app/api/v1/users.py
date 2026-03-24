from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.auth import CurrentUserResponse
from app.schemas.user import (
    ChangePasswordRequest,
    InviteUserRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from app.services.audit_service import AuditService
from app.services.tenant_settings_service import QuotaExceeded, TenantSettingsService
from app.services.user_service import UserService
from app.utils.exceptions import UserNotFound

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service = UserService(db)
    try:
        service.change_password(current_user, payload.current_password, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: InviteUserRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> UserResponse:
    # Check quota
    quota_svc = TenantSettingsService(db)
    try:
        quota_svc.check_user_quota(current_user.tenant_id)
    except QuotaExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    service = UserService(db)
    try:
        user = service.invite_user(
            tenant_id=current_user.tenant_id,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.USER_INVITE,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": payload.email, "role": payload.role.value if payload.role else "member"},
    )

    return UserResponse.model_validate(user)


@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> UserListResponse:
    service = UserService(db)
    users, total = service.list_tenant_users(current_user.tenant_id, skip=skip, limit=limit)
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        user = service.get_user(user_id, current_user.tenant_id)
    except UserNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UpdateUserRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        user = service.update_user(
            user_id,
            current_user.tenant_id,
            username=payload.username,
            role=payload.role,
            is_active=payload.is_active,
        )
    except UserNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    service = UserService(db)
    try:
        service.delete_user(user_id, current_user.tenant_id)
    except UserNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.USER_DELETE,
        resource_type="user",
        resource_id=str(user_id),
    )
