"""merge heads

Revision ID: merge_heads_001
Revises: add_subtask_completions, memories_friends_only
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_001'
down_revision = ('add_subtask_completions', 'memories_friends_only')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
