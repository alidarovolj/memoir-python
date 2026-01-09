"""add_memory_reactions_comments

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-31 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for reaction type (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reactiontype AS ENUM ('like', 'love', 'fire', 'star', 'celebrate', 'thinking');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create memory_reactions table
    op.create_table(
        'memory_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reaction_type', postgresql.ENUM('like', 'love', 'fire', 'star', 'celebrate', 'thinking', name='reactiontype', create_type=False), 
                  nullable=False, server_default='like'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_reactions_id'), 'memory_reactions', ['id'], unique=False)
    op.create_index(op.f('ix_memory_reactions_memory_id'), 'memory_reactions', ['memory_id'], unique=False)
    op.create_index(op.f('ix_memory_reactions_user_id'), 'memory_reactions', ['user_id'], unique=False)
    # Unique constraint: one reaction per user per memory
    op.create_unique_constraint('uq_user_memory_reaction', 'memory_reactions', ['user_id', 'memory_id'])
    
    # Create memory_comments table
    op.create_table(
        'memory_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['memory_comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_comments_id'), 'memory_comments', ['id'], unique=False)
    op.create_index(op.f('ix_memory_comments_memory_id'), 'memory_comments', ['memory_id'], unique=False)
    op.create_index(op.f('ix_memory_comments_user_id'), 'memory_comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_memory_comments_created_at'), 'memory_comments', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_memory_comments_created_at'), table_name='memory_comments')
    op.drop_index(op.f('ix_memory_comments_user_id'), table_name='memory_comments')
    op.drop_index(op.f('ix_memory_comments_memory_id'), table_name='memory_comments')
    op.drop_index(op.f('ix_memory_comments_id'), table_name='memory_comments')
    op.drop_table('memory_comments')
    
    op.drop_constraint('uq_user_memory_reaction', 'memory_reactions', type_='unique')
    op.drop_index(op.f('ix_memory_reactions_user_id'), table_name='memory_reactions')
    op.drop_index(op.f('ix_memory_reactions_memory_id'), table_name='memory_reactions')
    op.drop_index(op.f('ix_memory_reactions_id'), table_name='memory_reactions')
    op.drop_table('memory_reactions')
    
    # Drop enum type
    reaction_type = postgresql.ENUM('like', 'love', 'fire', 'star', 'celebrate', 'thinking', name='reactiontype')
    reaction_type.drop(op.get_bind(), checkfirst=True)
