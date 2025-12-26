"""create_tasks_table

Revision ID: 92389ddb0a57
Revises: 9301b389601e
Create Date: 2025-11-12 16:45:43.334810

Creates tasks table for task management CRUD operations.
Stores user-scoped tasks with status tracking and priority assignment.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '92389ddb0a57'
down_revision: Union[str, None] = '9301b389601e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('title', sa.VARCHAR(length=500), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('priority', sa.VARCHAR(length=50), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('due_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Single-column index for user-scoped queries
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'], unique=False)
    
    # Composite index for filtered queries (user_id + status)
    op.create_index('idx_tasks_user_status', 'tasks', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_tasks_user_status', table_name='tasks')
    op.drop_index('idx_tasks_user_id', table_name='tasks')
    op.drop_table('tasks')
