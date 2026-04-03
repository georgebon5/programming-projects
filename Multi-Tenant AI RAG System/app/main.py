"""
Main FastAPI application entry point.
"""

import logging
import platform
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.admin import router as admin_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.export import router as export_router
from app.api.v1.settings import router as settings_router
from app.api.v1.users import router as users_router
from app.config import settings
from app.db.database import engine, init_db
from app.utils.exceptions import (
    AccountLockedError,
    CustomException,
    DocumentNotFound,
    DocumentProcessingError,
    InvalidTenantAccess,
    TenantNotFound,
    UnauthorizedException,
    UserNotFound,
)
from app.utils.logging import setup_logging
from app.utils.middleware import BodySizeLimitMiddleware, RequestIDMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.utils.rate_limit import limiter

logger = logging.getLogger(__name__)

# Configure structured logging before anything else
setup_logging()

# ── Sentry (initialise before the app so all exceptions are captured) ─────────
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        # Never send PII — strip user IP addresses and request bodies
        send_default_pii=False,
    )
    logger.info("Sentry initialized (environment=%s)", settings.environment)

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    # ── Startup ──
    logger.info(
        "Starting Multi-Tenant AI RAG System v0.5.0 [%s]",
        settings.environment,
    )
    init_db()
    logger.info("Database tables initialized")
    # Initialize OpenTelemetry tracing (no-op if not configured)
    from app.utils.tracing import setup_tracing
    setup_tracing(app=app, engine=engine)
    yield
    # ── Shutdown ──
    logger.info("Shutting down — disposing database connections")
    engine.dispose()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Multi-Tenant AI RAG System",
    description="Production-ready backend for tenant-specific document AI queries",
    version="0.5.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Global Exception Handlers ────────────────────────────────────────────────
@app.exception_handler(TenantNotFound)
@app.exception_handler(UserNotFound)
@app.exception_handler(DocumentNotFound)
async def _not_found_handler(request: Request, exc: CustomException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc) or "Resource not found"})


@app.exception_handler(UnauthorizedException)
async def _unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})


@app.exception_handler(InvalidTenantAccess)
async def _forbidden_handler(request: Request, exc: InvalidTenantAccess) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc) or "Access denied"})


@app.exception_handler(AccountLockedError)
async def _account_locked_handler(request: Request, exc: AccountLockedError) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": str(exc) or "Account temporarily locked"})


@app.exception_handler(DocumentProcessingError)
async def _processing_error_handler(request: Request, exc: DocumentProcessingError) -> JSONResponse:
    logger.error("Document processing error: %s", exc)
    return JSONResponse(status_code=422, content={"detail": str(exc) or "Document processing failed"})


@app.exception_handler(SQLAlchemyError)
async def _database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal database error"})


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Request logging (outermost — sees final status code & timing)
app.add_middleware(RequestLoggingMiddleware)

# Request ID tracing
app.add_middleware(RequestIDMiddleware)

# Security headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Body size limit
app.add_middleware(BodySizeLimitMiddleware)

# Add CORS middleware (origins from CORS_ORIGINS env var)
_allow_creds = "*" not in settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=_allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(api_keys_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")

# ── Prometheus Metrics ─────────────────────────────────────────────────────────
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    excluded_handlers=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
    should_group_status_codes=True,
    should_group_untemplated=True,
).instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Liveness probe — lightweight, always responds."""
    return {"status": "healthy", "version": "0.5.0"}


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """Readiness probe — verifies dependencies (DB, etc.)."""
    checks: dict[str, str] = {}
    overall = True

    # Database connectivity
    try:
        from sqlalchemy import text
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        finally:
            db.close()
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        overall = False

    uptime = time.time() - _start_time
    payload = {
        "status": "ready" if overall else "degraded",
        "environment": settings.environment,
        "version": "0.5.0",
        "uptime_seconds": round(uptime, 1),
        "python_version": platform.python_version(),
        "checks": checks,
    }
    status_code = 200 if overall else 503
    return JSONResponse(status_code=status_code, content=payload)


# ── Frontend (SPA) ────────────────────────────────────────────────────────────
from pathlib import Path as _Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_frontend_dir = _Path(__file__).resolve().parent.parent / "frontend"

if _frontend_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/app/{rest_of_path:path}", include_in_schema=False)
    async def serve_spa(rest_of_path: str):
        """Serve the SPA index.html for all /app/* routes."""
        return FileResponse(str(_frontend_dir / "index.html"))

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """Redirect root to frontend."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/")
else:
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        return {
            "message": "Multi-Tenant AI RAG System API",
            "version": "0.5.0",
            "docs": "/docs" if settings.debug else "Not available in production",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
