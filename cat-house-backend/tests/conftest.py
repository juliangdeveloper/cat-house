"""
Shared testing configuration for Cat House backend services.

This configuration provides:
1. Neon test branch fixtures for isolated testing
2. Database session fixtures
3. Test data factories
4. MCP tool integration for branch management
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Import all models to ensure they're registered
import sys
from pathlib import Path

# Add service paths
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "auth-service"))
sys.path.insert(0, str(backend_dir / "catalog-service"))
sys.path.insert(0, str(backend_dir / "installation-service"))
sys.path.insert(0, str(backend_dir / "proxy-service"))


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Get database URL for testing.
    
    In development: Uses Neon development branch
    In CI/CD: Uses ephemeral test branch created by CI
    """
    # Check for CI environment test branch URL
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        return test_url
    
    # Otherwise use development branch
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set. Please configure .env files.")
    
    # For Neon, ensure we're using the development branch
    # The DATABASE_URL from .env should already point to the correct branch
    return database_url.replace("sslmode=require", "")  # Remove if present


@pytest.fixture(scope="session")
async def test_engine(test_database_url: str):
    """Create test database engine."""
    engine = create_async_engine(
        test_database_url,
        poolclass=NullPool,  # No pooling for tests
        echo=False,  # Disable SQL logging in tests
        connect_args={
            "ssl": "require",
            "server_settings": {
                "application_name": "cat-house-tests",
                "jit": "off",
            },
            "command_timeout": 60,
        }
    )
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.
    
    This fixture:
    1. Creates a new session
    2. Begins a transaction
    3. Yields the session to the test
    4. Rolls back the transaction after the test
    
    This ensures test isolation without actually modifying the database.
    """
    # Create session factory
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture(scope="function")
async def clean_db(db_session: AsyncSession):
    """
    Clean all tables before test.
    
    Use this fixture when you need a clean database state.
    """
    from sqlalchemy import text
    
    # Get all table names
    result = await db_session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name != 'alembic_version'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result.fetchall()]
    
    # Truncate all tables
    for table in reversed(tables):  # Reverse to handle foreign keys
        await db_session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
    
    await db_session.commit()
    return db_session


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def user_factory(db_session: AsyncSession):
    """Factory for creating test users."""
    from faker import Faker
    import uuid
    from datetime import datetime
    
    fake = Faker()
    
    async def create_user(**kwargs):
        """Create a test user with optional overrides."""
        from sqlalchemy import text
        
        user_data = {
            "id": kwargs.get("id", uuid.uuid4()),
            "email": kwargs.get("email", fake.email()),
            "password_hash": kwargs.get("password_hash", "hashed_password"),
            "role": kwargs.get("role", "player"),
            "display_name": kwargs.get("display_name", fake.name()),
            "is_active": kwargs.get("is_active", True),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            "updated_at": kwargs.get("updated_at", datetime.utcnow()),
        }
        
        result = await db_session.execute(text("""
            INSERT INTO users (id, email, password_hash, role, display_name, is_active, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :role, :display_name, :is_active, :created_at, :updated_at)
            RETURNING *
        """), user_data)
        
        await db_session.commit()
        return result.first()
    
    return create_user


@pytest.fixture
def cat_factory(db_session: AsyncSession):
    """Factory for creating test cats."""
    from faker import Faker
    import uuid
    from datetime import datetime
    
    fake = Faker()
    
    async def create_cat(developer_id: uuid.UUID, **kwargs):
        """Create a test cat with optional overrides."""
        from sqlalchemy import text
        
        cat_data = {
            "id": kwargs.get("id", uuid.uuid4()),
            "developer_id": developer_id,
            "name": kwargs.get("name", f"Test Cat {fake.word()}"),
            "description": kwargs.get("description", fake.text(max_nb_chars=200)),
            "version": kwargs.get("version", "1.0.0"),
            "endpoint_url": kwargs.get("endpoint_url", fake.url()),
            "status": kwargs.get("status", "published"),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            "updated_at": kwargs.get("updated_at", datetime.utcnow()),
        }
        
        result = await db_session.execute(text("""
            INSERT INTO cats (id, developer_id, name, description, version, endpoint_url, status, created_at, updated_at)
            VALUES (:id, :developer_id, :name, :description, :version, :endpoint_url, :status, :created_at, :updated_at)
            RETURNING *
        """), cat_data)
        
        await db_session.commit()
        return result.first()
    
    return create_cat


@pytest.fixture
def installation_factory(db_session: AsyncSession):
    """Factory for creating test installations."""
    from faker import Faker
    import uuid
    from datetime import datetime
    
    fake = Faker()
    
    async def create_installation(user_id: uuid.UUID, cat_id: uuid.UUID, **kwargs):
        """Create a test installation with optional overrides."""
        from sqlalchemy import text
        
        installation_data = {
            "id": kwargs.get("id", uuid.uuid4()),
            "user_id": user_id,
            "cat_id": cat_id,
            "instance_name": kwargs.get("instance_name", f"instance_{fake.word()}"),
            "config": kwargs.get("config", {}),
            "status": kwargs.get("status", "active"),
            "installed_at": kwargs.get("installed_at", datetime.utcnow()),
            "last_interaction_at": kwargs.get("last_interaction_at", datetime.utcnow()),
        }
        
        result = await db_session.execute(text("""
            INSERT INTO installations (id, user_id, cat_id, instance_name, config, status, installed_at, last_interaction_at)
            VALUES (:id, :user_id, :cat_id, :instance_name, :config, :status, :installed_at, :last_interaction_at)
            RETURNING *
        """), installation_data)
        
        await db_session.commit()
        return result.first()
    
    return create_installation


# ============================================================================
# Neon MCP Integration (for CI/CD)
# ============================================================================

@pytest.fixture(scope="session")
def neon_project_id() -> str:
    """Get Neon project ID from environment."""
    project_id = os.getenv("NEON_PROJECT_ID", "old-dew-33552653")
    return project_id


@pytest.fixture(scope="session")
def neon_test_branch_name() -> str:
    """Generate unique test branch name."""
    # Use CI run ID if available, otherwise generate UUID
    ci_run_id = os.getenv("CI_RUN_ID") or os.getenv("GITHUB_RUN_ID")
    if ci_run_id:
        return f"test-{ci_run_id}"
    return f"test-{uuid.uuid4().hex[:8]}"


# NOTE: For actual CI/CD integration, you would implement fixtures that:
# 1. Create a Neon branch before tests
# 2. Run migrations on the test branch
# 3. Return the test branch connection string
# 4. Clean up the test branch after tests
#
# Example (pseudo-code):
# @pytest.fixture(scope="session")
# async def neon_test_branch(neon_project_id, neon_test_branch_name):
#     """Create and cleanup Neon test branch."""
#     # Create branch using MCP
#     branch = create_neon_branch(neon_project_id, neon_test_branch_name)
#     
#     # Run migrations
#     run_migrations_on_branch(branch.id)
#     
#     # Set connection string for tests
#     os.environ["TEST_DATABASE_URL"] = branch.connection_url
#     
#     yield branch
#     
#     # Cleanup
#     delete_neon_branch(neon_project_id, branch.id)
