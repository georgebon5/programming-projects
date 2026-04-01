from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.services.api_key_service import APIKeyService
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.utils.security import TokenPayloadError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate via Bearer JWT **or** X-API-Key header."""

    # 1. Try X-API-Key header first
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        svc = APIKeyService(db)
        key_obj = svc.validate_key(api_key_header)
        if key_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
            )
        user = db.query(User).filter(User.id == key_obj.user_id).first()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user

    # 2. Fall back to Bearer JWT
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication: provide Bearer token or X-API-Key header",
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except TokenPayloadError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    # Check token blacklist (explicit revocation via logout)
    jti = payload["jti"]
    token_svc = TokenService(db)
    if token_svc.is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    auth_service = AuthService(db)
    user_id = UUID(payload["sub"])
    token_tenant_id = UUID(payload["tenant_id"])

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.tenant_id != token_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant context")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # Check if all tokens were revoked (e.g., after password change)
    if user.tokens_revoked_at is not None:
        token_iat = payload["iat"]
        # Reject tokens whose iat (integer seconds) is strictly before the
        # revocation second.  Tokens minted in the *same* second pass through;
        # this is acceptable because the only token that can share the second is
        # the one used for the password-change request itself, which the caller
        # is already holding and will discard.
        revoked_at_ts = int(user.tokens_revoked_at.replace(tzinfo=UTC).timestamp())
        if token_iat < revoked_at_ts:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked — please log in again",
            )

    return user


def require_role(allowed_roles: set[UserRole]) -> Callable[[User], User]:
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )
        return current_user

    return _role_checker
