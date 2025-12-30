"""Database connection and session management for proxy-service.

Connection Allocation (proxy-service):
- pool_size=1, max_overflow=0 (max 1 connection, read-only)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings

# Runtime async engine (smaller pool for proxy)
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_timeout=30,
    echo=settings.debug,
    connect_args={
        "ssl": "require",
        "server_settings": {
            "application_name": "cat-house-proxy-service",
            "jit": "off",
        },
        "command_timeout": 60,
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
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
    """Close database connections gracefully."""
    await engine.dispose()
