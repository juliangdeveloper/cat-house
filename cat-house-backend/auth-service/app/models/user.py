"""User model for authentication and user management.

Owner: auth-service
Purpose: Core user authentication, role management, and profile data
"""

from typing import Optional

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel


class User(Base, BaseModel):
    """User model for authentication and profile management.

    Roles:
    - 'player': Regular user who installs and uses cats
    - 'developer': Can create and publish cats
    - 'admin': Platform administrator

    Indexes:
    - UNIQUE on email (fast login lookups)
    - Composite on (role, is_active) for admin queries
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique)",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bcrypt hashed password"
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="User role: player, developer, or admin"
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="User's display name"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Account active status"
    )

    # Table arguments for composite indexes
    __table_args__ = (Index("ix_users_role_active", "role", "is_active"),)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
