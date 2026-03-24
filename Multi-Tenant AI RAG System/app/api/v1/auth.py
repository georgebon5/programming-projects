from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.auth import (
    CreateTenantAdminRequest,
    CurrentUserResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.utils.exceptions import AccountLockedError, PasswordValidationError
from app.utils.rate_limit import limiter
from app.utils.security import (
    TokenPayloadError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.config import settings as app_settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register-tenant-admin", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: app_settings.rate_limit_auth)
def register_tenant_admin(
    request: Request,
    payload: CreateTenantAdminRequest,
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    service = AuthService(db)
    try:
        user = service.register_tenant_with_admin(
            tenant_name=payload.tenant_name,
            tenant_slug=payload.tenant_slug,
            tenant_description=payload.tenant_description,
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
    except PasswordValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    audit = AuditService(db)
    audit.log(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action=AuditAction.REGISTER,
        resource_type="tenant",
        details={"tenant_name": payload.tenant_name},
        ip_address=request.client.host if request.client else None,
    )

    return CurrentUserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(lambda: app_settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    try:
        user = service.authenticate_user(email=payload.email, password=payload.password)
    except AccountLockedError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    audit = AuditService(db)
    audit.log(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action=AuditAction.LOGIN,
        ip_address=request.client.host if request.client else None,
    )

    token, expires = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    refresh, _ = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token, refresh_token=refresh, expires_in_seconds=expires)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(lambda: app_settings.rate_limit_login)
def refresh_token(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        claims = decode_refresh_token(payload.refresh_token)
    except TokenPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    from uuid import UUID
    user_id = UUID(claims["sub"])
    tenant_id = UUID(claims["tenant_id"])

    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if user is None or not user.is_active or user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_token, expires = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    new_refresh, _ = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id)
    return TokenResponse(access_token=new_token, refresh_token=new_refresh, expires_in_seconds=expires)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
