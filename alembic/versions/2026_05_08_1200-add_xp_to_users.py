"""add_xp_to_users

Revision ID: add_xp_to_users
Revises: 8d87fd3a05a4
Create Date: 2026-05-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_xp_to_users'
down_revision = '8d87fd3a05a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('xp', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'xp')
