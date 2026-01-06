from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Service configuration
    service_name: str = "catalog-service"
    service_display_name: str = "Catalog Service"
    debug: bool = False
    port: int = 8002
    environment: str = "development"

    # Database (Shared Neon PostgreSQL)
    database_url: str
    migration_database_url: Optional[str] = None  # For Alembic migrations (sync driver)

    # Connection pooling
    pool_size: int = 2
    max_overflow: int = 1

    # CORS
    allowed_origins: List[str] = ["https://app.gamificator.click"]

    # S3 Storage
    s3_bucket: str = "cathouse-assets"
    s3_region: str = "us-east-1"

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Invalid PostgreSQL URL format")
        return v


settings = Settings()
