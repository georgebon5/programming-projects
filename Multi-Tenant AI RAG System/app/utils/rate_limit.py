"""
Rate limiting middleware using SlowAPI.
Limits per-user (via JWT) to prevent API abuse.
"""

import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_user_identifier(request: Request) -> str:
    """
    Extract user identity from JWT token for per-user rate limiting.
    Falls back to IP address for unauthenticated requests.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # Use first 16 chars of token as identifier (unique enough, avoids storing full token)
        return f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(key_func=_get_user_identifier)
