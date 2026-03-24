"""
Configuration and environment variables for the application.
Uses pydantic-settings for type-safe configuration.
"""


from pydantic_settings import BaseSettings


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
    cors_origins: str = "*"  # Comma-separated origins, e.g. "https://app.example.com,https://admin.example.com"

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
    debug: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
