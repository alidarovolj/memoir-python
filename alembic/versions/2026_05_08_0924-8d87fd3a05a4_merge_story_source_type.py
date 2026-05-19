"""merge_story_source_type

Revision ID: 8d87fd3a05a4
Revises: merge_heads_001, add_story_source_type
Create Date: 2026-05-08 09:24:10.223265

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d87fd3a05a4'
down_revision = ('merge_heads_001', 'add_story_source_type')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

