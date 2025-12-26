from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )
    
    # Service configuration
    service_name: str = "Health Aggregator"
    environment: str = "development"
    port: int = 8000

settings = Settings()
