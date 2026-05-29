"""merge message media and xp heads

Revision ID: merge_message_media_heads
Revises: add_xp_to_users, 2026_05_29_1400
Create Date: 2026-05-29 14:30:00.000000
"""
from alembic import op

revision = "merge_message_media_heads"
down_revision = ("add_xp_to_users", "2026_05_29_1400")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
