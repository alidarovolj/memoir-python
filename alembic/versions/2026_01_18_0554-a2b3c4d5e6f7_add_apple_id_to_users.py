"""add_apple_id_to_users

Revision ID: a2b3c4d5e6f7
Revises: 9f8e7d6c5b4a
Create Date: 2026-01-18 05:54:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = '9f8e7d6c5b4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add apple_id column
    op.add_column('users', sa.Column('apple_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_apple_id'), 'users', ['apple_id'], unique=True)


def downgrade() -> None:
    # Remove apple_id
    op.drop_index(op.f('ix_users_apple_id'), table_name='users')
    op.drop_column('users', 'apple_id')
