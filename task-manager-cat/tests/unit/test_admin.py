"""
Unit tests for admin functionality.

Tests service key generation and admin key validation in isolation.
"""

import re
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.auth import generate_service_key, validate_admin_key


class TestServiceKeyGeneration:
    """Test generate_service_key function"""

    def test_generate_service_key_prod_format(self):
        """Verify prod keys have format sk_prod_{64 hex chars}"""
        key = generate_service_key('prod')
        assert re.match(r'^sk_prod_[0-9a-f]{64}$', key), f"Invalid format: {key}"

    def test_generate_service_key_dev_format(self):
        """Verify dev keys have format sk_dev_{64 hex chars}"""
        key = generate_service_key('dev')
        assert re.match(r'^sk_dev_[0-9a-f]{64}$', key), f"Invalid format: {key}"

    def test_generate_service_key_length(self):
        """Verify total length is correct (prefix + 64 hex)"""
        prod_key = generate_service_key('prod')
        dev_key = generate_service_key('dev')

        # sk_prod_ = 8 chars, sk_dev_ = 7 chars, hex = 64 chars
        assert len(prod_key) == 72, f"Expected 72 chars for prod, got {len(prod_key)}"
        assert len(dev_key) == 71, f"Expected 71 chars for dev, got {len(dev_key)}"

    def test_generate_service_key_uniqueness(self):
        """Generate 100 keys, verify all unique"""
        keys = [generate_service_key('prod') for _ in range(100)]
        assert len(set(keys)) == 100, "Generated keys are not unique"

    def test_generate_service_key_invalid_environment(self):
        """Verify ValueError for invalid environment"""
        with pytest.raises(ValueError) as exc_info:
            generate_service_key('staging')

        assert "Invalid environment: staging" in str(exc_info.value)
        assert "Must be 'prod' or 'dev'" in str(exc_info.value)


class TestAdminKeyValidation:
    """Test validate_admin_key dependency"""

    @pytest.mark.asyncio
    async def test_validate_admin_key_valid(self):
        """Valid admin key does not raise exception"""
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_api_key = 'test-admin-key'

            # Should not raise
            result = await validate_admin_key(x_admin_key='test-admin-key')
            assert result is None

    @pytest.mark.asyncio
    async def test_validate_admin_key_invalid(self):
        """Invalid admin key raises HTTPException(401)"""
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_api_key = 'correct-key'

            with pytest.raises(HTTPException) as exc_info:
                await validate_admin_key(x_admin_key='wrong-key')

            assert exc_info.value.status_code == 401
            assert "Invalid admin key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_admin_key_case_sensitive(self):
        """Admin key validation is case-sensitive"""
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_api_key = 'TestKey123'

            # Correct case should work
            result = await validate_admin_key(x_admin_key='TestKey123')
            assert result is None

            # Different case should fail
            with pytest.raises(HTTPException) as exc_info:
                await validate_admin_key(x_admin_key='testkey123')

            assert exc_info.value.status_code == 401
