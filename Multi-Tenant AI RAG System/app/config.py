"""
Configuration and environment variables for the application.
Uses pydantic-settings for type-safe configuration.
"""

import logging
import sys

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./test.db"

    # JWT & Security
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OpenAI
    openai_api_key: str | None = None

    # File Storage
    upload_dir: str = "./local_uploads"
    max_file_size_mb: int = 50

    # Vector DB
    vector_db_path: str = "./vector_db"
    embedding_model: str = "text-embedding-3-small"

    # CORS
    cors_origins: str = "http://localhost:3000"  # Comma-separated origins

    # Chat
    chat_max_question_chars: int = 4000

    # Email (leave email_host empty to use console backend in development)
    email_host: str = ""
    email_port: int = 587
    email_use_tls: bool = True
    email_username: str = ""
    email_password: str = ""
    email_from: str = "noreply@example.com"
    frontend_url: str = "http://localhost:8000"
    password_reset_expire_minutes: int = 30

    # Security
    password_min_length: int = 8
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15

    # Rate Limits (requests per minute)
    rate_limit_auth: str = "5/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_chat: str = "20/minute"
    rate_limit_default: str = "60/minute"

    # Environment
    environment: str = "development"
    debug: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()

# ── Production safety checks ─────────────────────────────────────────────────
if settings.environment == "production":
    if settings.jwt_secret_key == "dev-secret-key-change-in-production":
        logger.critical("FATAL: JWT_SECRET_KEY is still the default dev key in production!")
        sys.exit(1)
    if settings.debug:
        logger.warning("DEBUG is enabled in production — disable it for safety.")
