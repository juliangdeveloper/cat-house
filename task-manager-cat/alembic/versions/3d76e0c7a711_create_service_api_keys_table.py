"""create_service_api_keys_table

Revision ID: 3d76e0c7a711
Revises: 
Create Date: 2025-11-12 13:54:33.936234

Creates service_api_keys table for Service API Key authentication.
Stores API keys for authorized client applications (Cat House, mobile apps).

Table columns:
- id: UUID primary key (auto-generated)
- key_name: Unique identifier for the client (e.g., 'cat-house-prod')
- api_key: The actual service key (e.g., 'sk_prod_abc123...')
- active: Boolean flag to enable/disable keys without deletion
- created_at: Timestamp when key was created
- expires_at: Optional expiration timestamp (NULL for non-expiring keys)

Includes partial index on api_key WHERE active = true for performance.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3d76e0c7a711'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create service_api_keys table and index."""
    op.create_table(
        'service_api_keys',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('key_name', sa.VARCHAR(length=100), nullable=False),
        sa.Column('api_key', sa.VARCHAR(length=255), nullable=False),
        sa.Column('active', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_name'),
        sa.UniqueConstraint('api_key')
    )
    
    # Partial index for active key lookups (only indexes rows where active = true)
    op.create_index(
        'idx_service_api_keys_active',
        'service_api_keys',
        ['api_key'],
        unique=False,
        postgresql_where=sa.text('active = true')
    )


def downgrade() -> None:
    """Drop service_api_keys table and index."""
    op.drop_index('idx_service_api_keys_active', table_name='service_api_keys')
    op.drop_table('service_api_keys')
