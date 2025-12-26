"""
Task Manager API - Database Connection Management

Provides asyncpg connection pool and FastAPI dependency for database access.
Connection pool lifecycle is managed at application startup/shutdown.
"""

from typing import AsyncGenerator

import asyncpg

from app.config import settings

# Global connection pool (initialized at application startup)
_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create the asyncpg connection pool.
    
    Connection pool configuration:
    - min_size=2: Minimum connections maintained in pool
    - max_size=10: Maximum concurrent connections (suitable for development)
    - command_timeout=60: Query timeout in seconds
    
    The pool should be created once at application startup and reused
    for all database operations.
    
    Returns:
        asyncpg.Pool: Database connection pool
    
    Example:
        >>> pool = await get_db_pool()
        >>> async with pool.acquire() as conn:
        ...     result = await conn.fetchrow("SELECT 1 as value")
        ...     print(result['value'])
        1
    """
    global _pool

    if _pool is None:
        # Clean database_url: asyncpg doesn't accept postgresql+asyncpg:// scheme
        # Convert postgresql+asyncpg:// to postgresql:// for asyncpg compatibility
        db_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')

        _pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )

    return _pool


async def close_db_pool() -> None:
    """
    Close the database connection pool.
    
    Should be called at application shutdown to gracefully close
    all database connections.
    """
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency that provides a database connection from the pool.
    
    Acquires a connection from the pool for the duration of the request
    and automatically releases it when the request completes.
    
    Yields:
        asyncpg.Connection: Database connection from pool
    
    Usage in FastAPI endpoint:
        >>> from fastapi import Depends
        >>> from app.database import get_db
        >>> 
        >>> @app.get("/users/{user_id}")
        >>> async def get_user(user_id: str, db: asyncpg.Connection = Depends(get_db)):
        ...     result = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        ...     return result
    """
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection
