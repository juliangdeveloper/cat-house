"""Installation model for user cat installations.

Owner: installation-service
Purpose: Track user's installed cats with configuration and status
"""
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from .base import Base, BaseModel


class Installation(Base, BaseModel):
    """Installation model for user cat installations.
    
    Status values:
    - 'active': Cat is installed and active
    - 'paused': Cat is temporarily disabled
    - 'uninstalled': Cat has been uninstalled
    
    Indexes:
    - UNIQUE on (user_id, cat_id, instance_name)
    - Composite on (user_id, status) for user dashboard
    - On last_interaction_at for cleanup jobs
    """
    __tablename__ = "installations"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="Cat owner (FK to users.id)"
    )
    
    cat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cats.id', ondelete='RESTRICT'),
        nullable=False,
        comment="Installed cat (FK to cats.id)"
    )
    
    instance_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User-defined instance name"
    )
    
    config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Installation-specific configuration (JSON)"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Installation status: active, paused, uninstalled"
    )
    
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Installation timestamp (UTC)"
    )
    
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last usage timestamp (UTC)"
    )
    
    # Relationships
    # user = relationship("User", back_populates="installations")
    # cat = relationship("Cat", back_populates="installations")
    # permissions = relationship("InstallationPermission", back_populates="installation")
    
    # Table arguments for constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'cat_id', 'instance_name', name='uq_user_cat_instance'),
        Index('ix_installations_user_status', 'user_id', 'status'),
        Index('ix_installations_last_interaction', 'last_interaction_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Installation(id={self.id}, user_id={self.user_id}, cat_id={self.cat_id}, status={self.status})>"
