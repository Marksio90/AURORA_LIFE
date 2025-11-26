"""
Aurora Life Compass - Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Optional
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with production security validation"""

    # Application
    APP_NAME: str = "Aurora Life Compass"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False  # Default to False for security
    API_PORT: int = 8000
    SECRET_KEY: Optional[str] = None  # Must be set via environment variable

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aurora_life"
    POSTGRES_USER: str = "aurora"
    POSTGRES_PASSWORD: Optional[str] = None  # Must be set via environment variable

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # OAuth (optional - only needed if OAuth is enabled)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @model_validator(mode='after')
    def validate_production_settings(self):
        """Validate that production environment has secure configuration"""
        if self.APP_ENV == "production":
            errors = []

            # Validate SECRET_KEY
            if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
                errors.append("SECRET_KEY must be set to a secure random value in production")

            if self.SECRET_KEY and len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY must be at least 32 characters long")

            # Validate POSTGRES_PASSWORD
            if not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD == "aurora_dev_password":
                errors.append("POSTGRES_PASSWORD must be set to a secure password in production")

            # Validate DEBUG is off
            if self.APP_DEBUG:
                errors.append("APP_DEBUG must be False in production")

            # Validate CORS origins
            if "http://localhost:3000" in self.CORS_ORIGINS:
                logger.warning("localhost in CORS_ORIGINS for production environment")

            if errors:
                raise ValueError(
                    f"Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
                )

        # Generate SECRET_KEY for development if not set
        if self.APP_ENV == "development" and not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
            logger.warning("Generated temporary SECRET_KEY for development. Set SECRET_KEY in .env for persistence.")

        # Set default password for development if not set
        if self.APP_ENV == "development" and not self.POSTGRES_PASSWORD:
            self.POSTGRES_PASSWORD = "aurora_dev_password"
            logger.info("Using default development POSTGRES_PASSWORD")

        return self

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
