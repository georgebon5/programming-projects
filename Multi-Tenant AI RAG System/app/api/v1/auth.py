from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    CreateTenantAdminRequest,
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.rate_limit import limiter
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register-tenant-admin", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
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
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CurrentUserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    user = service.authenticate_user(email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, expires = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    return TokenResponse(access_token=token, expires_in_seconds=expires)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
