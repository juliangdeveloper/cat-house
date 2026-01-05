"""InstallationPermission model for granted permissions.

Owner: installation-service
Purpose: Track which permissions have been granted for each installation
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class InstallationPermission(Base):
    """InstallationPermission model for permission grants.

    This is a junction table with additional metadata about when
    permissions were granted.

    Composite Primary Key: (installation_id, permission_id)
    """

    __tablename__ = "installation_permissions"
    __table_args__ = (
        Index("ix_installation_permissions_inst_perm", "installation_id", "permission_id"),
        {"schema": "installation"},
    )

    installation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("installations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Installation reference (FK to installations.id within installation schema)",
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Permission reference (logical reference to catalog.permissions.id - validated at application level)",
    )

    granted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Permission granted status"
    )

    granted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When permission was granted (UTC)",
    )

    # Relationships
    # installation = relationship("Installation", back_populates="permissions")
    # permission = relationship("Permission")

    # Table arguments for composite primary key
    __table_args__ = (
        PrimaryKeyConstraint(
            "installation_id", "permission_id", name="pk_installation_permissions"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InstallationPermission(installation_id={self.installation_id}, "
            f"permission_id={self.permission_id}, granted={self.granted})>"
        )
