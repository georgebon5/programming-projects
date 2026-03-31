"""
Rate limiting middleware using SlowAPI.
Limits per-tenant so all users of the same tenant share a quota.
This prevents a single tenant from bypassing limits via multiple user accounts.
Falls back to per-IP for unauthenticated requests.
"""

import base64
import hashlib
import json
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

logger = logging.getLogger(__name__)


def _get_tenant_identifier(request: Request) -> str:
    """
    Extract tenant_id from JWT payload for per-tenant rate limiting.
    JWT payload is decoded without signature verification (the actual auth
    validates the token; here we only need a stable bucket key).
    Falls back to IP address for unauthenticated or invalid requests.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1]
                # Restore base64 padding
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                tenant_id = payload.get("tenant_id")
                if tenant_id:
                    return f"tenant:{tenant_id}"
        except Exception:
            logger.debug("Rate limiter: could not decode JWT payload, falling back to token hash")
        # Fallback: per-user bucket (hashed token, avoids storing the raw token)
        return f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"

    # Unauthenticated: limit by IP
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(key_func=_get_tenant_identifier)
