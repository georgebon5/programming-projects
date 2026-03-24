"""
Middleware that attaches a unique request ID to every request/response.
Enables distributed tracing and log correlation.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID into every request and response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Honour client-provided ID (e.g. from API gateway), or generate one
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
