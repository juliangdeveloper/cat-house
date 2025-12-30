"""Permission model for cat permission definitions.

Owner: catalog-service
Purpose: Define permissions required by cats
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel


class Permission(Base, BaseModel):
    """Permission model for cat permission definitions.

    Permission types:
    - 'storage': Access to user storage
    - 'notification': Send notifications to user
    - 'external_api': Call external APIs on user's behalf

    Indexes:
    - Composite on (cat_id, permission_type) for permission lookups
    """

    __tablename__ = "permissions"

    cat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cats.id", ondelete="CASCADE"),
        nullable=False,
        comment="Associated cat (FK to cats.id)",
    )

    permission_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Permission type: storage, notification, external_api",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Permission description for users"
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this permission mandatory for cat to function",
    )

    # Relationships
    # cat = relationship("Cat", back_populates="permissions")

    # Table arguments for composite indexes
    __table_args__ = (Index("ix_permissions_cat_type", "cat_id", "permission_type"),)

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, cat_id={self.cat_id}, type={self.permission_type})>"
