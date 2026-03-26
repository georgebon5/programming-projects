from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.auth import (
    CreateTenantAdminRequest,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TOTPCodeRequest,
    TOTPSetupResponse,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.email_verification_service import EmailVerificationService
from app.services.password_reset_service import PasswordResetService
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

    # Send email verification
    EmailVerificationService(db).send_verification(user)

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

    # Check 2FA if enabled
    if user.totp_enabled:
        if not payload.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
                headers={"X-2FA-Required": "true"},
            )
        from app.services.totp_service import TwoFactorService
        totp_svc = TwoFactorService(db)
        if not totp_svc.verify_code(user, payload.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
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


# ── Password Reset ────────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(lambda: app_settings.rate_limit_auth)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Request a password reset email.

    Always returns 202 to prevent email enumeration.
    """
    svc = PasswordResetService(db)
    svc.request_reset(payload.email)
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit(lambda: app_settings.rate_limit_auth)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Reset password using a valid reset token."""
    svc = PasswordResetService(db)
    try:
        svc.reset_password(payload.token, payload.new_password)
    except PasswordValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"detail": "Password has been reset successfully."}


# ── Email Verification ────────────────────────────────────────────────────────

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Confirm a user's email address using the token from the verification email."""
    svc = EmailVerificationService(db)
    try:
        svc.verify(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"detail": "Email verified successfully."}


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(lambda: app_settings.rate_limit_auth)
def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Resend the verification email to the current user."""
    if current_user.is_email_verified:
        return {"detail": "Email is already verified."}
    EmailVerificationService(db).send_verification(current_user)
    return {"detail": "Verification email sent."}


# ── Two-Factor Authentication ────────────────────────────────────────────────

@router.post("/2fa/enable", response_model=TOTPSetupResponse)
def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TOTPSetupResponse:
    """Generate a TOTP secret and QR code for two-factor authentication setup."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")
    from app.services.totp_service import TwoFactorService
    svc = TwoFactorService(db)
    result = svc.generate_secret(current_user)
    return TOTPSetupResponse(**result)


@router.post("/2fa/verify", status_code=status.HTTP_200_OK)
def verify_2fa(
    payload: TOTPCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Verify a TOTP code and activate 2FA for the current user."""
    from app.services.totp_service import TwoFactorService
    svc = TwoFactorService(db)
    if not svc.verify_and_enable(current_user, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    return {"detail": "Two-factor authentication enabled successfully."}


@router.post("/2fa/disable", status_code=status.HTTP_200_OK)
def disable_2fa(
    payload: TOTPCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Disable 2FA for the current user (requires a valid TOTP code)."""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")
    from app.services.totp_service import TwoFactorService
    svc = TwoFactorService(db)
    if not svc.disable(current_user, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    return {"detail": "Two-factor authentication disabled."}
