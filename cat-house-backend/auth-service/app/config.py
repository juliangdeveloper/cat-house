from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )
    
    # Service configuration
    service_name: str = "Auth Service"
    debug: bool = False
    port: int = 8005
    environment: str = "development"
    
    # Database (Shared Neon PostgreSQL)
    database_url: str
    migration_database_url: Optional[str] = None  # Only auth-service needs this
    
    # Connection pooling
    pool_size: int = 2
    max_overflow: int = 1
    
    # Authentication
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # CORS
    allowed_origins: List[str] = ["https://app.gamificator.click"]
    
    @field_validator('database_url')
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('Invalid PostgreSQL URL format')
        return v

settings = Settings()
