"""initial schema

Revision ID: cd0f2927ee5e
Revises: 
Create Date: 2025-12-05 18:20:02.035578+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cd0f2927ee5e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table in auth schema
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False, comment='User email address (unique)'),
    sa.Column('password_hash', sa.String(length=255), nullable=False, comment='Bcrypt hashed password'),
    sa.Column('role', sa.String(length=20), nullable=False, comment='User role: player, developer, or admin'),
    sa.Column('display_name', sa.String(length=100), nullable=True, comment="User's display name"),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='Account active status'),
    sa.Column('id', sa.UUID(), nullable=False, comment='Unique identifier (UUID v4)'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Record creation timestamp (UTC)'),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='Record last update timestamp (UTC)'),
    sa.PrimaryKeyConstraint('id'),
    schema='auth'
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True, schema='auth')
    op.create_index('ix_users_role_active', 'users', ['role', 'is_active'], unique=False, schema='auth')


def downgrade() -> None:
    op.drop_index('ix_users_role_active', table_name='users', schema='auth')
    op.drop_index(op.f('ix_users_email'), table_name='users', schema='auth')
    op.drop_table('users', schema='auth')

