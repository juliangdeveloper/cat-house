from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Service configuration
    service_name: str = "Installation Service"
    debug: bool = False
    port: int = 8003
    environment: str = "development"

    # Database (Shared Neon PostgreSQL)
    database_url: str

    # Connection pooling
    pool_size: int = 2
    max_overflow: int = 1

    # CORS
    allowed_origins: List[str] = ["https://app.gamificator.click"]

    # Encryption
    # SECURITY: No default value - must be set via environment variable
    # Generate with: openssl rand -hex 32 (must be exactly 32 characters)
    encryption_key: str

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate encryption key length."""
        if len(v) != 32:
            raise ValueError("Encryption key must be exactly 32 characters")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Invalid PostgreSQL URL format")
        return v


settings = Settings()
