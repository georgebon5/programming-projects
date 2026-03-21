from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import settings


class TokenPayloadError(ValueError):
    pass


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


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenPayloadError("Invalid or expired token") from exc

    required_fields = {"sub", "tenant_id", "role", "exp"}
    if not required_fields.issubset(payload.keys()):
        raise TokenPayloadError("Token payload is missing required claims")

    return payload
