"""add linkedin_url to users

Revision ID: add_linkedin_url
Revises: add_personal_data
Create Date: 2026-01-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_linkedin_url'
down_revision = 'add_personal_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('linkedin_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'linkedin_url')
