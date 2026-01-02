"""Base SQLAlchemy models for Cat House.

This module defines the base classes used by all models across all services.
Following Neon AI Rules best practices for serverless PostgreSQL.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models with async support.

    This base class enables async operations with SQLAlchemy 2.0+
    and provides the foundation for all models in the shared database.
    """


class BaseModel:
    """Base model mixin with common fields for all entities.

    Provides:
    - UUID primary keys (better for distributed systems)
    - Automatic timestamps (UTC timezone)
    - Consistent field naming across all tables

    Usage:
        class User(Base, BaseModel):
            __tablename__ = 'users'
            email: Mapped[str] = mapped_column(String(255), unique=True)
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier (UUID v4)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Record creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Record last update timestamp (UTC)",
    )

    def dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Useful for serialization to JSON responses.
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
