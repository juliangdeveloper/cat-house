"""
Integration tests for admin endpoints.

Tests admin endpoints with real database and HTTP requests.
"""

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import close_db_pool
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Provide test database connection"""
    conn = await asyncpg.connect(
        "postgresql://taskuser:taskpass@postgres:5432/taskmanager_dev"
    )
    # Clear test data before test
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")
    yield conn
    # Clear test data after test
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")
    await conn.close()


@pytest_asyncio.fixture(scope="function")
async def test_client():
    """Provide HTTP client for testing"""
    # Close any existing pool before starting test
    await close_db_pool()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Close pool after test to avoid event loop issues
    await close_db_pool()


class TestCreateServiceKey:
    """Test POST /admin/service-keys endpoint"""

    @pytest.mark.asyncio
    async def test_create_service_key_success(self, test_client, test_db):
        """Valid request creates key and returns correct response"""
        response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-client-prod", "environment": "prod"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["key_name"] == "test-client-prod"
        assert data["service_key"].startswith("sk_prod_")
        assert len(data["service_key"]) == 72  # sk_prod_ (8 chars) + 64 hex
        assert "created_at" in data

        # Verify database state
        row = await test_db.fetchrow(
            "SELECT * FROM service_api_keys WHERE key_name = $1",
            "test-client-prod"
        )
        assert row is not None
        assert row['active'] is True
        assert row['api_key'] == data["service_key"]
        assert row['expires_at'] is None

    @pytest.mark.asyncio
    async def test_create_service_key_dev_environment(self, test_client, test_db):
        """Creating dev key uses sk_dev_ prefix"""
        response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-client-dev", "environment": "dev"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["service_key"].startswith("sk_dev_")

    @pytest.mark.asyncio
    async def test_create_service_key_duplicate_name(self, test_client, test_db):
        """Duplicate key_name returns 400"""
        # Create first key
        await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-duplicate", "environment": "prod"}
        )

        # Try to create duplicate
        response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-duplicate", "environment": "prod"}
        )

        assert response.status_code == 400
        assert "test-duplicate" in response.json()["detail"]
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_service_key_no_admin_key(self, test_client):
        """Request without X-Admin-Key returns 401"""
        response = await test_client.post(
            "/admin/service-keys",
            json={"key_name": "test-noauth", "environment": "prod"}
        )

        assert response.status_code == 422  # FastAPI validation error for missing header

    @pytest.mark.asyncio
    async def test_create_service_key_invalid_admin_key(self, test_client):
        """Invalid X-Admin-Key returns 401"""
        response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "wrong-admin-key"},
            json={"key_name": "test-wrongauth", "environment": "prod"}
        )

        assert response.status_code == 401
        assert "Invalid admin key" in response.json()["detail"]


class TestRotateServiceKey:
    """Test POST /admin/rotate-key endpoint"""

    @pytest.mark.asyncio
    async def test_rotate_key_success(self, test_client, test_db):
        """Valid rotation updates old key expiration and creates new key"""
        # Create initial key
        create_response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-rotate", "environment": "prod"}
        )
        old_key = create_response.json()["service_key"]

        # Rotate key
        rotate_response = await test_client.post(
            "/admin/rotate-key",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-rotate"}
        )

        assert rotate_response.status_code == 200
        data = rotate_response.json()

        # Verify response
        assert "new_key" in data
        assert data["new_key"].startswith("sk_prod_")
        assert data["new_key"] != old_key
        assert "old_key_expires_at" in data

        # Verify old key has expiration set
        old_row = await test_db.fetchrow(
            "SELECT * FROM service_api_keys WHERE api_key = $1",
            old_key
        )
        assert old_row is not None
        assert old_row['expires_at'] is not None

        # Verify new key exists without expiration
        new_row = await test_db.fetchrow(
            "SELECT * FROM service_api_keys WHERE api_key = $1",
            data["new_key"]
        )
        assert new_row is not None
        assert new_row['expires_at'] is None
        assert new_row['active'] is True

    @pytest.mark.asyncio
    async def test_rotate_key_preserves_environment(self, test_client, test_db):
        """Rotated key preserves environment from old key"""
        # Create dev key
        await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-rotate-dev", "environment": "dev"}
        )

        # Rotate
        rotate_response = await test_client.post(
            "/admin/rotate-key",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-rotate-dev"}
        )

        # New key should also be dev
        data = rotate_response.json()
        assert data["new_key"].startswith("sk_dev_")

    @pytest.mark.asyncio
    async def test_rotate_key_nonexistent(self, test_client):
        """Rotating non-existent key returns 404"""
        response = await test_client.post(
            "/admin/rotate-key",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-nonexistent"}
        )

        assert response.status_code == 404
        assert "test-nonexistent" in response.json()["detail"]
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rotate_key_no_admin_key(self, test_client):
        """Request without X-Admin-Key returns 422"""
        response = await test_client.post(
            "/admin/rotate-key",
            json={"key_name": "test-noauth"}
        )

        assert response.status_code == 422  # FastAPI validation error

    @pytest.mark.asyncio
    async def test_rotate_key_invalid_admin_key(self, test_client):
        """Invalid X-Admin-Key returns 401"""
        response = await test_client.post(
            "/admin/rotate-key",
            headers={"X-Admin-Key": "wrong-admin-key"},
            json={"key_name": "test-wrongauth"}
        )

        assert response.status_code == 401
        assert "Invalid admin key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_expired_key_validation(self, test_client, test_db):
        """Verify validate_service_key rejects expired keys after rotation"""
        # Create and rotate key
        create_response = await test_client.post(
            "/admin/service-keys",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-expire", "environment": "dev"}
        )
        old_key = create_response.json()["service_key"]

        await test_client.post(
            "/admin/rotate-key",
            headers={"X-Admin-Key": "dev-admin-key-replace-in-production"},
            json={"key_name": "test-expire"}
        )

        # Manually set old key to expired (past date)
        await test_db.execute(
            "UPDATE service_api_keys SET expires_at = NOW() - INTERVAL '1 day' WHERE api_key = $1",
            old_key
        )

        # Verify old key no longer validates
        result = await test_db.fetchrow("""
            SELECT key_name FROM service_api_keys 
            WHERE api_key = $1 
            AND active = true 
            AND (expires_at IS NULL OR expires_at > NOW())
        """, old_key)

        assert result is None, "Expired key should not validate"
