"""initial schema

Revision ID: 20260105_0001
Revises: 
Create Date: 2026-01-05 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260105_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cats table in catalog schema
    op.create_table('cats',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('developer_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Cat developer (logical reference to auth.users.id - validated at application level)'),
    sa.Column('name', sa.String(length=100), nullable=False, comment='Cat name'),
    sa.Column('description', sa.Text(), nullable=True, comment='Cat description'),
    sa.Column('version', sa.String(length=20), nullable=False, comment='Cat version (semver)'),
    sa.Column('status', sa.String(length=20), nullable=False, comment='Cat status: draft, published, deprecated'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='catalog'
    )
    op.create_index('ix_cats_developer_status', 'cats', ['developer_id', 'status'], unique=False, schema='catalog')
    op.create_index('ix_cats_status', 'cats', ['status'], unique=False, schema='catalog')

    # Create permissions table in catalog schema
    op.create_table('permissions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('cat_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Associated cat (FK to cats.id within catalog schema)'),
    sa.Column('permission_type', sa.String(length=50), nullable=False, comment='Permission type: storage, notification, external_api'),
    sa.Column('scope', sa.String(length=100), nullable=True, comment='Permission scope details'),
    sa.Column('description', sa.Text(), nullable=True, comment='Permission description'),
    sa.Column('required', sa.Boolean(), nullable=False, comment='Is this permission required?'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['cat_id'], ['catalog.cats.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='catalog'
    )
    op.create_index('ix_permissions_cat_type', 'permissions', ['cat_id', 'permission_type'], unique=False, schema='catalog')


def downgrade() -> None:
    op.drop_index('ix_permissions_cat_type', table_name='permissions', schema='catalog')
    op.drop_table('permissions', schema='catalog')
    op.drop_index('ix_cats_status', table_name='cats', schema='catalog')
    op.drop_index('ix_cats_developer_status', table_name='cats', schema='catalog')
    op.drop_table('cats', schema='catalog')
