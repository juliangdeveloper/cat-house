"""
Unit tests for Service API Key authentication (app/auth.py).

Tests validate_service_key dependency with various scenarios:
- Valid active keys
- Invalid/missing keys
- Inactive keys
- Expired keys
- Keys with future expiration

Uses real database connection with test data cleanup.
"""

from datetime import datetime, timedelta, timezone

import asyncpg
import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.auth import validate_service_key
from app.config import settings


@pytest_asyncio.fixture
async def test_db():
    """
    Provide a clean database connection for each test.
    
    Creates connection, yields it for test use, then cleans up test data.
    """
    # Strip +asyncpg dialect from URL for asyncpg.connect()
    database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn=database_url)

    # Clean up any existing test data
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")

    yield conn

    # Clean up test data after test
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")
    await conn.close()


@pytest.mark.asyncio
async def test_validate_service_key_valid(test_db):
    """Test that valid active service key returns key_name."""
    # Insert test key
    await test_db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, expires_at)
        VALUES ('test-client-valid', 'sk_test_valid_key_abc123', true, NULL)
    """)

    # Validate key
    key_name = await validate_service_key(
        x_service_key="sk_test_valid_key_abc123",
        db=test_db
    )

    assert key_name == "test-client-valid"


@pytest.mark.asyncio
async def test_validate_service_key_invalid(test_db):
    """Test that invalid/non-existent service key raises 401."""
    # Try to validate non-existent key
    with pytest.raises(HTTPException) as exc_info:
        await validate_service_key(
            x_service_key="sk_test_nonexistent_key",
            db=test_db
        )

    assert exc_info.value.status_code == 401
    assert "invalid or expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_service_key_inactive(test_db):
    """Test that inactive service key (active=false) raises 401."""
    # Insert inactive key
    await test_db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, expires_at)
        VALUES ('test-client-inactive', 'sk_test_inactive_key_xyz789', false, NULL)
    """)

    # Try to validate inactive key
    with pytest.raises(HTTPException) as exc_info:
        await validate_service_key(
            x_service_key="sk_test_inactive_key_xyz789",
            db=test_db
        )

    assert exc_info.value.status_code == 401
    assert "invalid or expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_service_key_expired(test_db):
    """Test that expired service key (expires_at < NOW) raises 401."""
    # Insert expired key (expired 1 day ago)
    expired_time = datetime.now(timezone.utc) - timedelta(days=1)
    await test_db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, expires_at)
        VALUES ('test-client-expired', 'sk_test_expired_key_def456', true, $1)
    """, expired_time)

    # Try to validate expired key
    with pytest.raises(HTTPException) as exc_info:
        await validate_service_key(
            x_service_key="sk_test_expired_key_def456",
            db=test_db
        )

    assert exc_info.value.status_code == 401
    assert "invalid or expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_service_key_not_expired(test_db):
    """Test that valid key with future expiration succeeds."""
    # Insert key expiring in 30 days
    future_time = datetime.now(timezone.utc) + timedelta(days=30)
    await test_db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, expires_at)
        VALUES ('test-client-future', 'sk_test_future_key_ghi789', true, $1)
    """, future_time)

    # Validate key with future expiration
    key_name = await validate_service_key(
        x_service_key="sk_test_future_key_ghi789",
        db=test_db
    )

    assert key_name == "test-client-future"


@pytest.mark.asyncio
async def test_validate_service_key_null_expiration(test_db):
    """Test that key with NULL expires_at (non-expiring) succeeds."""
    # Insert non-expiring key
    await test_db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, expires_at)
        VALUES ('test-client-permanent', 'sk_test_permanent_key_jkl012', true, NULL)
    """)

    # Validate non-expiring key
    key_name = await validate_service_key(
        x_service_key="sk_test_permanent_key_jkl012",
        db=test_db
    )

    assert key_name == "test-client-permanent"
