"""add_group_challenges

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-12-31 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create group_challenges table
    op.create_table(
        'group_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('goal', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(50), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_challenges_id'), 'group_challenges', ['id'], unique=False)
    
    # Create group_challenge_members association table
    op.create_table(
        'group_challenge_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['challenge_id'], ['group_challenges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create group_challenge_invites table
    op.create_table(
        'group_challenge_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('inviter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['challenge_id'], ['group_challenges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inviter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invitee_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_challenge_invites_id'), 'group_challenge_invites', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_group_challenge_invites_id'), table_name='group_challenge_invites')
    op.drop_table('group_challenge_invites')
    op.drop_table('group_challenge_members')
    op.drop_index(op.f('ix_group_challenges_id'), table_name='group_challenges')
    op.drop_table('group_challenges')
