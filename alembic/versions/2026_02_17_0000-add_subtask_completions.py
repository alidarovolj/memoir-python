"""add subtask_completions table

Revision ID: add_subtask_completions
Revises: add_messages_table
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_subtask_completions"
down_revision = "add_messages_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subtask_completions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subtask_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("subtasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subtask_completions_task_subtask", "subtask_completions", ["task_id", "subtask_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_subtask_completions_task_subtask", table_name="subtask_completions")
    op.drop_table("subtask_completions")
