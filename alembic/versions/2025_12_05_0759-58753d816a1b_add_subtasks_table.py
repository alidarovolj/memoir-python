"""add_subtasks_table

Revision ID: 58753d816a1b
Revises: dd0b605e2086
Create Date: 2025-12-05 07:59:27.523944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58753d816a1b'
down_revision = 'dd0b605e2086'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subtasks table
    op.create_table(
        'subtasks',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for better query performance
    op.create_index('ix_subtasks_task_id', 'subtasks', ['task_id'])
    op.create_index('ix_subtasks_order', 'subtasks', ['task_id', 'order'])


def downgrade() -> None:
    # Drop indexes if they exist
    op.execute('DROP INDEX IF EXISTS ix_subtasks_order')
    op.execute('DROP INDEX IF EXISTS ix_subtasks_task_id')
    
    # Drop table if it exists
    op.execute('DROP TABLE IF EXISTS subtasks')

