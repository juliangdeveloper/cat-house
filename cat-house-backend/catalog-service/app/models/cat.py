"""Cat model for cat metadata and discovery.

Owner: catalog-service
Purpose: Cat definition, versioning, and publication status
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel


class Cat(Base, BaseModel):
    """Cat model for catalog and discovery.

    Status values:
    - 'draft': Cat is being developed, not visible to users
    - 'published': Cat is available for installation
    - 'suspended': Cat is temporarily disabled

    Indexes:
    - On status for filtering published cats
    - Composite on (developer_id, status) for developer dashboard
    """

    __tablename__ = "cats"

    developer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Cat developer (FK to users.id)",
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Cat name")

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cat description"
    )

    version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Semantic version (e.g., 1.0.0)"
    )

    endpoint_url: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Cat API endpoint URL"
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Cat status: draft, published, suspended"
    )

    # Relationships
    # developer = relationship("User", back_populates="cats")
    # permissions = relationship("Permission", back_populates="cat", cascade="all, delete-orphan")

    # Table arguments for composite indexes
    __table_args__ = (
        Index("ix_cats_status", "status"),
        Index("ix_cats_developer_status", "developer_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Cat(id={self.id}, name={self.name}, status={self.status})>"
