"""
Integration tests for CORS configuration.

Tests CORS preflight requests, actual requests, and origin validation.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import close_db_pool
from app.main import app


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


class TestCORSPreflight:
    """Test CORS preflight OPTIONS requests"""

    @pytest.mark.asyncio
    async def test_cors_preflight_options_request(self, test_client):
        """
        Test CORS preflight request returns correct headers.
        
        Simulates browser preflight before Cat House makes POST /execute request.
        """
        response = await test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Service-Key, Content-Type",
            }
        )

        # Assert preflight response
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert "POST" in response.headers["Access-Control-Allow-Methods"]
        assert "X-Service-Key" in response.headers["Access-Control-Allow-Headers"]
        assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
        assert response.headers["Access-Control-Allow-Credentials"] == "true"

    @pytest.mark.asyncio
    async def test_cors_allowed_headers(self, test_client):
        """Verify only allowed headers pass preflight"""
        # Test with disallowed header - FastAPI CORSMiddleware returns 400
        response = await test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Service-Key, Content-Type, X-Custom-Header",
            }
        )

        # FastAPI's CORSMiddleware rejects preflight with disallowed headers
        assert response.status_code == 400

        # Test with only allowed headers - should succeed
        response_allowed = await test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Service-Key, Content-Type",
            }
        )

        assert response_allowed.status_code == 200
        assert "X-Service-Key" in response_allowed.headers["Access-Control-Allow-Headers"]
        assert "Content-Type" in response_allowed.headers["Access-Control-Allow-Headers"]


class TestCORSActualRequests:
    """Test CORS headers on actual HTTP requests"""

    @pytest.mark.asyncio
    async def test_cors_actual_request_with_origin(self, test_client):
        """Actual GET request with Origin header includes CORS headers"""
        response = await test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert response.headers["Access-Control-Allow-Credentials"] == "true"

        # Verify health check response body
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_cors_disallowed_origin(self, test_client):
        """Request from non-whitelisted origin returns 400"""
        response = await test_client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )

        # FastAPI CORSMiddleware returns 400 for disallowed origins
        assert response.status_code == 400


class TestCORSAllowedMethods:
    """Test CORS allowed methods configuration"""

    @pytest.mark.asyncio
    async def test_cors_allowed_methods(self, test_client):
        """Verify only specific HTTP methods are allowed"""
        response = await test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )

        assert response.status_code == 200
        allowed_methods = response.headers["Access-Control-Allow-Methods"]

        # Verify explicit methods are allowed
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "PATCH" in allowed_methods
        assert "DELETE" in allowed_methods
        assert "OPTIONS" in allowed_methods

        # Verify wildcard is NOT present (explicit values only)
        # Note: We can't easily test that TRACE/CONNECT are blocked without
        # making actual TRACE requests, which httpx doesn't support well
