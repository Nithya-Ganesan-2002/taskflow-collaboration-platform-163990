from functools import lru_cache
import logging
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Uses Pydantic BaseSettings to read from environment (.env) with defaults.
    Supports SQLite (default) and can be swapped to Postgres via DATABASE_URL.
    """
    # App
    APP_NAME: str = Field(default="TaskFlow API", description="Application name for the API")
    APP_DESCRIPTION: str = Field(default="Backend API for TaskFlow collaboration platform", description="API description")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Enable debug mode")

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Database
    # For SQLite async default; can be overridden by env DATABASE_URL
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./taskflow.db",
        description="SQLAlchemy database URL",
    )

    # Security / Auth
    SECRET_KEY: str = Field(default="CHANGE_ME", description="Secret key for signing JWTs")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="Refresh token expiration in minutes")

    class Config:
        env_file = ".env"
        case_sensitive = True


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    settings = Settings()  # type: ignore[call-arg]
    # Basic bootstrap logging level based on DEBUG
    logging.getLogger().setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    return settings
