"""add messages table

Revision ID: add_messages_table
Revises: 2026_01_26_1400-add_linkedin_url_to_users
Create Date: 2026-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_messages_table'
down_revision = 'add_linkedin_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_receiver_id', 'messages', ['receiver_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_receiver_id', table_name='messages')
    op.drop_index('ix_messages_sender_id', table_name='messages')
    
    # Drop table
    op.drop_table('messages')
