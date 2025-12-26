from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
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
    encryption_key: str = "changeme-32-characters-long!!"
    
    @field_validator('database_url')
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('Invalid PostgreSQL URL format')
        return v

settings = Settings()
