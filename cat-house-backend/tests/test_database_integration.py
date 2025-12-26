"""
Example integration tests demonstrating database testing patterns.

These tests show how to:
1. Use database fixtures
2. Use test data factories
3. Test across multiple tables
4. Verify database constraints
"""
import pytest
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Test basic database connectivity."""
    result = await db_session.execute(text("SELECT 1 as test"))
    row = result.first()
    assert row[0] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_user(clean_db, user_factory):
    """Test creating a user using the factory."""
    # Create user
    user = await user_factory(
        email="test@example.com",
        display_name="Test User"
    )
    
    # Verify user was created
    assert user is not None
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.role == "player"  # Default value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_cat_with_developer(clean_db, user_factory, cat_factory):
    """Test creating a cat with a developer relationship."""
    # Create developer
    developer = await user_factory(
        email="dev@example.com",
        role="developer"
    )
    
    # Create cat
    cat = await cat_factory(
        developer_id=developer.id,
        name="Test Cat",
        description="A test cat for testing"
    )
    
    # Verify cat was created
    assert cat is not None
    assert cat.name == "Test Cat"
    assert cat.developer_id == developer.id
    assert cat.status == "published"  # Default value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_installation(clean_db, user_factory, cat_factory, installation_factory):
    """Test creating an installation with relationships."""
    # Create user
    user = await user_factory(email="player@example.com")
    
    # Create developer
    developer = await user_factory(email="dev@example.com", role="developer")
    
    # Create cat
    cat = await cat_factory(
        developer_id=developer.id,
        name="Game Cat"
    )
    
    # Create installation
    installation = await installation_factory(
        user_id=user.id,
        cat_id=cat.id,
        instance_name="my_game_instance"
    )
    
    # Verify installation was created
    assert installation is not None
    assert installation.user_id == user.id
    assert installation.cat_id == cat.id
    assert installation.instance_name == "my_game_instance"
    assert installation.status == "active"  # Default value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unique_constraint(clean_db, user_factory, cat_factory, installation_factory):
    """Test that unique constraint on (user_id, cat_id, instance_name) works."""
    # Create user and cat
    user = await user_factory()
    developer = await user_factory(role="developer")
    cat = await cat_factory(developer_id=developer.id)
    
    # Create first installation
    await installation_factory(
        user_id=user.id,
        cat_id=cat.id,
        instance_name="instance1"
    )
    
    # Try to create duplicate installation (should fail)
    with pytest.raises(Exception):  # Would be IntegrityError in real scenario
        await installation_factory(
            user_id=user.id,
            cat_id=cat.id,
            instance_name="instance1"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_with_relationships(clean_db, user_factory, cat_factory, installation_factory):
    """Test querying data with relationships."""
    # Setup test data
    user = await user_factory(email="player@example.com")
    developer = await user_factory(email="dev@example.com", role="developer")
    cat = await cat_factory(developer_id=developer.id, name="Test Cat")
    installation = await installation_factory(
        user_id=user.id,
        cat_id=cat.id,
        instance_name="test_instance"
    )
    
    # Query installation with joined data
    query = text("""
        SELECT 
            i.id as installation_id,
            i.instance_name,
            u.email as user_email,
            c.name as cat_name,
            d.email as developer_email
        FROM installations i
        JOIN users u ON i.user_id = u.id
        JOIN cats c ON i.cat_id = c.id
        JOIN users d ON c.developer_id = d.id
        WHERE i.id = :installation_id
    """)
    
    result = await clean_db.execute(query, {"installation_id": installation.id})
    row = result.first()
    
    # Verify joined data
    assert row is not None
    assert row.user_email == "player@example.com"
    assert row.cat_name == "Test Cat"
    assert row.developer_email == "dev@example.com"
    assert row.instance_name == "test_instance"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_count_tables(db_session):
    """Test that all expected tables exist."""
    query = text("""
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('users', 'cats', 'permissions', 'installations', 'installation_permissions')
    """)
    
    result = await db_session.execute(query)
    row = result.first()
    
    # Should have all 5 main tables
    assert row.table_count == 5
