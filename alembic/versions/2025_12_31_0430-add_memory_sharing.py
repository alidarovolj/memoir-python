"""add_memory_sharing

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-31 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for privacy level (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE privacylevel AS ENUM ('private', 'friends_only', 'shared', 'public');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add privacy_level column to memories table
    op.add_column('memories', 
        sa.Column('privacy_level', postgresql.ENUM('private', 'friends_only', 'shared', 'public', name='privacylevel', create_type=False), 
                  nullable=False, server_default='private')
    )
    
    # Create memory_shares association table
    op.create_table(
        'memory_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('can_comment', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_react', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_shares_memory_id'), 'memory_shares', ['memory_id'], unique=False)
    op.create_index(op.f('ix_memory_shares_shared_with_user_id'), 'memory_shares', ['shared_with_user_id'], unique=False)
    
    # Create memory_share_history table
    op.create_table(
        'memory_share_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_share_history_id'), 'memory_share_history', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_memory_share_history_id'), table_name='memory_share_history')
    op.drop_table('memory_share_history')
    
    op.drop_index(op.f('ix_memory_shares_shared_with_user_id'), table_name='memory_shares')
    op.drop_index(op.f('ix_memory_shares_memory_id'), table_name='memory_shares')
    op.drop_table('memory_shares')
    
    # Drop column
    op.drop_column('memories', 'privacy_level')
    
    # Drop enum type
    privacy_level = postgresql.ENUM('private', 'friends_only', 'shared', 'public', name='privacylevel')
    privacy_level.drop(op.get_bind(), checkfirst=True)
