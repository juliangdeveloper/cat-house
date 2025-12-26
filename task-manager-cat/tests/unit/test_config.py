"""
Unit tests for app/config.py - Configuration management

Tests cover:
- Required field validation (DATABASE_URL)
- Database URL format validation
- CORS origins parsing
- Default values
- Environment variable loading

Note: Tests use _env_file=None and override DATABASE_URL to avoid loading .env.dev
"""

import pytest
from pydantic import ValidationError

from app.config import Settings


class TestSettingsValidation:
    """Test Settings class validation behavior"""

    def test_settings_requires_database_url(self, monkeypatch):
        """Test that Settings initialization fails without DATABASE_URL"""
        # Clear any existing DATABASE_URL from environment
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)

        error = exc_info.value
        assert "database_url" in str(error)
        assert "Field required" in str(error)

    def test_settings_validates_database_url_format_mysql(self):
        """Test that DATABASE_URL must be PostgreSQL (rejects MySQL)"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                database_url="mysql://user:pass@host/db",
                environment="test",
            )

        error = exc_info.value
        assert "postgresql" in str(error).lower()
        assert "mysql" in str(error).lower()

    def test_settings_validates_database_url_format_mongodb(self):
        """Test that DATABASE_URL must be PostgreSQL (rejects MongoDB)"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                database_url="mongodb://user:pass@host/db",
                environment="test",
            )

        error = exc_info.value
        assert "postgresql" in str(error).lower()

    def test_settings_accepts_valid_postgresql_url(self):
        """Test that Settings accepts standard postgresql:// URL"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://user:pass@host:5432/db",
            environment="test",
        )

        assert settings.database_url == "postgresql://user:pass@host:5432/db"

    def test_settings_accepts_valid_postgresql_asyncpg_url(self):
        """Test that Settings accepts postgresql+asyncpg:// URL"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://user:pass@host:5432/db?sslmode=require",
            environment="test",
        )

        assert (
            settings.database_url
            == "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require"
        )


class TestSettingsDefaults:
    """Test Settings default values"""

    def test_settings_has_default_environment(self):
        """Test that environment defaults to 'development'"""
        settings = Settings(
            _env_file=None, database_url="postgresql://host/db"
        )

        assert settings.environment == "development"

    def test_settings_has_default_log_level(self, monkeypatch):
        """Test that log_level defaults to 'INFO'"""
        # Clear environment variables
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        settings = Settings(
            _env_file=None, database_url="postgresql://host/db"
        )

        assert settings.log_level == "INFO"

    def test_settings_has_default_port(self):
        """Test that port defaults to 8000"""
        settings = Settings(
            _env_file=None, database_url="postgresql://host/db"
        )

        assert settings.port == 8000

    def test_settings_has_default_cors_origins(self, monkeypatch):
        """Test that cors_origins defaults to localhost:3000"""
        # Clear environment variables
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        settings = Settings(
            _env_file=None, database_url="postgresql://host/db"
        )

        assert settings.cors_origins == "http://localhost:3000"


class TestCORSOriginsListParsing:
    """Test CORS origins comma-separated string parsing"""

    def test_cors_origins_list_single_origin(self):
        """Test parsing a single CORS origin"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            cors_origins="http://localhost:3000",
        )

        origins = settings.get_cors_origins_list()
        assert origins == ["http://localhost:3000"]
        assert len(origins) == 1

    def test_cors_origins_list_multiple_origins(self):
        """Test parsing multiple CORS origins"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            cors_origins="http://localhost:3000,https://app.com,https://api.app.com",
        )

        origins = settings.get_cors_origins_list()
        assert origins == [
            "http://localhost:3000",
            "https://app.com",
            "https://api.app.com",
        ]
        assert len(origins) == 3

    def test_cors_origins_list_strips_whitespace(self):
        """Test that whitespace is stripped from CORS origins"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            cors_origins="  http://localhost:3000  ,  https://app.com  ",
        )

        origins = settings.get_cors_origins_list()
        assert origins == ["http://localhost:3000", "https://app.com"]
        # Verify no leading/trailing whitespace
        for origin in origins:
            assert origin == origin.strip()

    def test_cors_origins_list_empty_string(self):
        """Test parsing empty CORS origins string"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            cors_origins="",
        )

        origins = settings.get_cors_origins_list()
        assert origins == [""]
        assert len(origins) == 1


class TestSettingsOverrides:
    """Test that environment variables override defaults"""

    def test_settings_environment_can_be_overridden(self):
        """Test overriding environment setting"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            environment="production",
        )

        assert settings.environment == "production"

    def test_settings_log_level_can_be_overridden(self):
        """Test overriding log_level setting"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql://host/db",
            log_level="DEBUG",
        )

        assert settings.log_level == "DEBUG"

    def test_settings_all_fields_can_be_set(self):
        """Test setting all configuration fields"""
        settings = Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://user:pass@host:5432/db",
            migration_database_url="postgresql://user:pass@host:5432/db",
            environment="staging",
            log_level="WARNING",
            port=9000,
            cors_origins="https://staging.app.com,https://api.staging.app.com",
            api_key_secret="test-secret-key-min-32-characters-long",
            admin_api_key="test-admin-key",
        )

        assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/db"
        assert settings.migration_database_url == "postgresql://user:pass@host:5432/db"
        assert settings.environment == "staging"
        assert settings.log_level == "WARNING"
        assert settings.port == 9000
        assert settings.cors_origins == "https://staging.app.com,https://api.staging.app.com"
        assert settings.api_key_secret == "test-secret-key-min-32-characters-long"
        assert settings.admin_api_key == "test-admin-key"
