"""Database connection and session management for auth-service.

This module configures SQLAlchemy async engine with Neon-specific settings:
- Connection pooling optimized for serverless
- Pre-ping to handle scale-to-zero gracefully
- Proper pool recycling to prevent stale connections

Connection Allocation (auth-service):
- pool_size=2, max_overflow=1 (max 3 connections)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine

from .config import settings


# Runtime async engine (for application use)
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_recycle=3600,  # CRITICAL: Recycle before scale-to-zero (1 hour)
    pool_pre_ping=True,  # REQUIRED: Validates connection before use
    pool_timeout=30,  # Connection acquisition timeout
    echo=settings.debug,  # SQL logging in debug mode
    connect_args={
        "ssl": "require",  # SSL required for Neon (asyncpg uses 'ssl' not 'sslmode')
        "server_settings": {
            "application_name": "cat-house-auth-service",
            "jit": "off",  # Faster cold starts in serverless
        },
        "command_timeout": 60,  # Query timeout
    },
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Migration engine (sync, direct endpoint, NO pooling)
# Only used by Alembic for migrations
def get_migration_engine():
    """Get sync engine for Alembic migrations.

    Uses:
    - Direct endpoint (not pooler)
    - Sync driver (psycopg2)
    - NullPool (no connection pooling)
    """
    if not settings.migration_database_url:
        raise ValueError("MIGRATION_DATABASE_URL not configured")

    return create_engine(
        settings.migration_database_url,
        poolclass=NullPool,
        echo=settings.debug,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connections gracefully.

    Call this on application shutdown.
    """
    await engine.dispose()
