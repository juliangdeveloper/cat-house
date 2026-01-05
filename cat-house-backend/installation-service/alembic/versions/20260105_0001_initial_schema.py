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
    # Create installations table in installation schema
    op.create_table('installations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Cat owner (logical reference to auth.users.id - validated at application level)'),
    sa.Column('cat_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Installed cat (logical reference to catalog.cats.id - validated at application level)'),
    sa.Column('instance_name', sa.String(length=100), nullable=True, comment='User-defined instance name'),
    sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Installation-specific configuration (JSON)'),
    sa.Column('status', sa.String(length=20), nullable=False, comment='Installation status: active, suspended, uninstalled'),
    sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True, comment='Last user interaction timestamp'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'cat_id', name='uq_user_cat'),
    schema='installation'
    )
    op.create_index('ix_installations_last_interaction', 'installations', ['last_interaction_at'], unique=False, schema='installation')
    op.create_index('ix_installations_user_status', 'installations', ['user_id', 'status'], unique=False, schema='installation')

    # Create installation_permissions table in installation schema
    op.create_table('installation_permissions',
    sa.Column('installation_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Installation reference (FK to installations.id within installation schema)'),
    sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Permission reference (logical reference to catalog.permissions.id - validated at application level)'),
    sa.Column('granted', sa.Boolean(), nullable=False, comment='Permission granted status'),
    sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True, comment='When permission was granted'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['installation_id'], ['installation.installations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('installation_id', 'permission_id'),
    schema='installation'
    )
    op.create_index('ix_installation_permissions_inst_perm', 'installation_permissions', ['installation_id', 'permission_id'], unique=False, schema='installation')


def downgrade() -> None:
    op.drop_index('ix_installation_permissions_inst_perm', table_name='installation_permissions', schema='installation')
    op.drop_table('installation_permissions', schema='installation')
    op.drop_index('ix_installations_user_status', table_name='installations', schema='installation')
    op.drop_index('ix_installations_last_interaction', table_name='installations', schema='installation')
    op.drop_table('installations', schema='installation')
