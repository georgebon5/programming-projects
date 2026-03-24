"""
Main FastAPI application entry point.
"""

import platform
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.db.database import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.settings import router as settings_router
from app.config import settings
from app.utils.rate_limit import limiter

_start_time = time.time()

# Initialize database tables
init_db()

# Create FastAPI app
app = FastAPI(
    title="Multi-Tenant AI RAG System",
    description="Production-ready backend for tenant-specific document AI queries",
    version="0.2.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Enhanced health check with system metrics."""
    uptime = time.time() - _start_time
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.2.0",
        "uptime_seconds": round(uptime, 1),
        "python_version": platform.python_version(),
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Multi-Tenant AI RAG System API",
        "version": "0.2.0",
        "docs": "/docs" if settings.debug else "Not available in production"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
