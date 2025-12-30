from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Service configuration
    service_name: str = "Cat Proxy Service"
    debug: bool = False
    port: int = 8004
    environment: str = "development"

    # Database (Shared Neon PostgreSQL - read-only)
    database_url: str

    # Connection pooling (smaller for proxy)
    pool_size: int = 1
    max_overflow: int = 0

    # CORS
    allowed_origins: List[str] = ["https://app.gamificator.click"]

    # Request configuration
    request_timeout: int = 30
    max_retries: int = 3

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Invalid PostgreSQL URL format")
        return v


settings = Settings()
