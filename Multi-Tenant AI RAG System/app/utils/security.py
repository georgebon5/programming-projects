import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.utils.exceptions import PasswordValidationError


class TokenPayloadError(ValueError):
    pass


def validate_password_strength(password: str) -> None:
    """Enforce password complexity rules based on config."""
    min_len = settings.password_min_length
    errors: list[str] = []
    if len(password) < min_len:
        errors.append(f"Password must be at least {min_len} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":\{\}|<>]", password):
        errors.append("Password must contain at least one special character")
    if errors:
        raise PasswordValidationError("; ".join(errors))


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(*, user_id: UUID, tenant_id: UUID, role: str) -> tuple[str, int]:
    expires_delta = timedelta(hours=settings.jwt_expiration_hours)
    expire_at = datetime.now(UTC) + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": int(expire_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(*, user_id: UUID, tenant_id: UUID) -> tuple[str, int]:
    """Create a long-lived refresh token (7 days)."""
    expires_delta = timedelta(days=7)
    expire_at = datetime.now(UTC) + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "exp": int(expire_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenPayloadError("Invalid or expired token") from exc

    required_fields = {"sub", "tenant_id", "role", "exp"}
    if not required_fields.issubset(payload.keys()):
        raise TokenPayloadError("Token payload is missing required claims")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenPayloadError("Invalid or expired refresh token") from exc

    if payload.get("type") != "refresh":
        raise TokenPayloadError("Token is not a refresh token")

    required_fields = {"sub", "tenant_id", "exp"}
    if not required_fields.issubset(payload.keys()):
        raise TokenPayloadError("Refresh token is missing required claims")

    return payload
