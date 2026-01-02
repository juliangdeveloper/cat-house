"""Tests for configuration loading and environment variables."""
import pytest
from app.config import Settings


def test_settings_defaults():
    """Test that settings have appropriate default values."""
    settings = Settings()
    
    assert settings.service_name == "auth-service"
    assert settings.service_display_name == "Auth Service"
    assert settings.debug is False
    assert settings.port == 8005
    assert isinstance(settings.allowed_origins, list)
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_minutes == 60


def test_settings_can_be_overridden(monkeypatch):
    """Test that settings can be overridden via environment variables."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("SERVICE_NAME", "Test Auth Service")
    
    settings = Settings()
    
    assert settings.debug is True
    assert settings.port == 9000
    assert settings.service_name == "Test Auth Service"


def test_database_url_configurable(monkeypatch):
    """Test that database URL can be configured."""
    test_url = "postgresql://test:test@localhost/test_db"
    monkeypatch.setenv("DATABASE_URL", test_url)
    
    settings = Settings()
    
    assert settings.database_url == test_url


def test_jwt_config_customizable(monkeypatch):
    """Test that JWT configuration is customizable."""
    monkeypatch.setenv("JWT_SECRET", "super-secret-key")
    monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "120")
    
    settings = Settings()
    
    assert settings.jwt_secret == "super-secret-key"
    assert settings.jwt_expiration_minutes == 120
