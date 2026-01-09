"""add_friendships_table

Revision ID: a1b2c3d4e5f6
Revises: 71bfa4fc736f
Create Date: 2025-12-31 04:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '71bfa4fc736f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for friendship status (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE friendshipstatus AS ENUM ('pending', 'accepted', 'rejected', 'blocked');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create friendships table
    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('addressee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'accepted', 'rejected', 'blocked', name='friendshipstatus', create_type=False), 
                  nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['addressee_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('requester_id', 'addressee_id', name='uq_friendship_pair')
    )
    op.create_index(op.f('ix_friendships_id'), 'friendships', ['id'], unique=False)


def downgrade() -> None:
    # Drop table
    op.drop_index(op.f('ix_friendships_id'), table_name='friendships')
    op.drop_table('friendships')
    
    # Drop enum type
    friendship_status = postgresql.ENUM('pending', 'accepted', 'rejected', 'blocked', name='friendshipstatus')
    friendship_status.drop(op.get_bind(), checkfirst=True)
