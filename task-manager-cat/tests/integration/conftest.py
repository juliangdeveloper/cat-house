"""
Pytest configuration for integration tests.

Provides shared fixtures for integration testing:
- test_db: Real database connection with cleanup
- client: Async HTTP client for API testing
- test_service_key: Valid service key for authentication
"""

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import generate_service_key
from app.database import close_db_pool
from app.main import app


# Configure pytest-asyncio to use function scope by default
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for all tests."""
    import asyncio
    return asyncio.get_event_loop_policy()


@pytest_asyncio.fixture(scope="function")
async def async_test():
    """Ensure each test gets its own event loop."""
    yield


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    Provide real database connection for integration tests.
    
    Automatically cleans up test data before and after each test.
    Test data is identified by user_id or key_name patterns starting with 'test-'.
    """
    conn = await asyncpg.connect(
        "postgresql://taskuser:taskpass@postgres:5432/taskmanager_dev"
    )

    # Clean up test data before test
    await conn.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")

    yield conn

    # Clean up test data after test
    await conn.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
    await conn.execute("DELETE FROM service_api_keys WHERE key_name LIKE 'test-%'")
    await conn.close()


@pytest_asyncio.fixture(scope="function")
async def client():
    """
    Provide async HTTP client for API integration testing.
    
    Uses httpx.AsyncClient with ASGITransport to test FastAPI app
    without requiring a running server. Automatically closes database
    pool before and after each test to avoid event loop issues.
    """
    # Close any existing pool before starting test
    await close_db_pool()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Close pool after test to avoid event loop issues
    await close_db_pool()


@pytest_asyncio.fixture(scope="function")
async def test_service_key(test_db):
    """
    Create test service key for authentication in integration tests.
    
    Generates a valid dev environment service key and inserts it into
    the database. Automatically cleaned up by test_db fixture.
    
    Returns:
        str: Valid service key that can be used in X-Service-Key header
    """
    key = generate_service_key('dev')
    await test_db.execute(
        """
        INSERT INTO service_api_keys (key_name, api_key, active)
        VALUES ($1, $2, $3)
        """,
        "test-client", key, True
    )
    return key
