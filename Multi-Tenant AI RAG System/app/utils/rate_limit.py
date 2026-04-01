"""
Rate limiting middleware using SlowAPI.
Priority:
  1. X-API-Key header  → per-key bucket (first 12 chars of the key)
  2. Bearer JWT        → per-tenant bucket (tenant_id from payload)
  3. Unauthenticated   → per-IP bucket
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
    Return a stable bucket key for rate limiting.

    - X-API-Key present  → ``apikey:<first-12-chars>``
    - Bearer JWT present → ``tenant:<tenant_id>`` (or ``user:<hash>`` fallback)
    - Otherwise          → remote IP address
    """
    # 1. API key — rate limit per individual key
    api_key = request.headers.get("X-API-Key")
    if api_key and len(api_key) >= 12:
        return f"apikey:{api_key[:12]}"

    # 2. JWT — rate limit per tenant
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

    # 3. Unauthenticated: limit by IP
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(key_func=_get_tenant_identifier)
