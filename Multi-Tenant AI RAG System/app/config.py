"""
Configuration and environment variables for the application.
Uses pydantic-settings for type-safe configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/multi_tenant_rag"
    
    # JWT & Security
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # File Storage
    upload_dir: str = "./local_uploads"
    max_file_size_mb: int = 50
    
    # Vector DB
    vector_db_path: str = "./vector_db"
    embedding_model: str = "text-embedding-3-small"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
