"""add message media support

Revision ID: 2026_05_29_1400
Revises: 2026_05_26_1400
Create Date: 2026-05-29 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_05_29_1400"
down_revision = "add_space_sync_task_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "message_type",
            sa.String(length=20),
            nullable=False,
            server_default="text",
        ),
    )
    op.add_column(
        "messages",
        sa.Column("media_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "media_url")
    op.drop_column("messages", "message_type")
