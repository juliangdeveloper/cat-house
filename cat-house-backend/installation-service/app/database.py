"""Database connection and session management for installation-service.

Connection Allocation (installation-service):
- pool_size=2, max_overflow=1 (max 3 connections)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .config import settings


# Runtime async engine
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
            "application_name": "cat-house-installation-service",
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
