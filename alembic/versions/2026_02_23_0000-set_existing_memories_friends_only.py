"""set existing memories to friends_only so they appear in friends' feed

Revision ID: memories_friends_only
Revises: add_messages_table
Create Date: 2026-02-23

"""
from alembic import op

revision = 'memories_friends_only'
down_revision = 'add_messages_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Сделать все текущие private-воспоминания видимыми друзьям (friends_only)
    op.execute("""
        UPDATE memories
        SET privacy_level = 'friends_only'
        WHERE privacy_level = 'private'
    """)


def downgrade() -> None:
    # Вернуть обратно в private (при необходимости)
    op.execute("""
        UPDATE memories
        SET privacy_level = 'private'
        WHERE privacy_level = 'friends_only'
    """)
