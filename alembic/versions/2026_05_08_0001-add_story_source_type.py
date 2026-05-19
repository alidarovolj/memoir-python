"""add story source_type value

Revision ID: add_story_source_type
Revises: add_linkedin_url
Create Date: 2026-05-08 00:01:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_story_source_type'
down_revision = 'add_linkedin_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS 'story'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    pass
