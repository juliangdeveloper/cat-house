"""
Task Manager API - Configuration Management

Type-safe configuration loading from environment variables using Pydantic Settings.
All required variables are validated on application startup (fail-fast principle).
"""

from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    Required fields (no default):
        - database_url: PostgreSQL connection string for asyncpg
    
    Optional fields (with defaults):
        - environment: Runtime environment (development, staging, production)
        - log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - port: Internal container port
        - migration_database_url: Direct PostgreSQL connection for Alembic
        - cors_origins: Comma-separated allowed origins
        - api_key_secret: Secret for API key generation (Epic 2)
        - admin_api_key: Admin endpoint authentication (Epic 2)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    # Database settings
    database_url: str  # REQUIRED - no default value
    migration_database_url: Optional[str] = None

    # CORS settings
    cors_origins: str = "http://localhost:3000"

    # Authentication settings (Epic 2)
    api_key_secret: Optional[str] = None
    admin_api_key: str  # REQUIRED - no default value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate that database_url uses PostgreSQL protocol.
        
        Args:
            v: Database URL string to validate
            
        Returns:
            Validated database URL
            
        Raises:
            ValueError: If database URL doesn't start with postgresql:// or postgresql+asyncpg://
        """
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgresql+asyncpg://. "
                f"Got: {v[:20]}..."
            )
        return v

    def get_cors_origins_list(self) -> list[str]:
        """
        Parse comma-separated CORS origins into a list.
        
        Returns:
            List of origin URLs with whitespace stripped
            
        Example:
            >>> settings = Settings(cors_origins="http://localhost:3000, https://app.com")
            >>> settings.get_cors_origins_list()
            ['http://localhost:3000', 'https://app.com']
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Singleton instance - import this in other modules
settings = Settings()  # type: ignore[call-arg]
