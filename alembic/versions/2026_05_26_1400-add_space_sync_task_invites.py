"""add_space_sync_task_invites

Revision ID: add_space_sync_task_invites
Revises: add_space_syncs
Create Date: 2026-05-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_space_sync_task_invites"
down_revision = "add_space_syncs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE spacesynctaskinvitestatus AS ENUM ('pending', 'accepted', 'rejected');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.create_table(
        "space_sync_task_invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "accepted",
                "rejected",
                name="spacesynctaskinvitestatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "to_user_id", name="uq_space_sync_task_invite"),
    )
    op.create_index(
        op.f("ix_space_sync_task_invites_id"),
        "space_sync_task_invites",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_space_sync_task_invites_task_id"),
        "space_sync_task_invites",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_space_sync_task_invites_to_user_id"),
        "space_sync_task_invites",
        ["to_user_id"],
        unique=False,
    )

    # Backfill accepted invites for tasks that existed before per-task sharing
    op.execute(
        """
        INSERT INTO space_sync_task_invites
            (task_id, from_user_id, to_user_id, status, created_at, responded_at)
        SELECT
            t.id,
            t.user_id,
            CASE
                WHEN ss.requester_id = t.user_id THEN ss.partner_id
                ELSE ss.requester_id
            END,
            'accepted',
            NOW(),
            NOW()
        FROM space_syncs ss
        JOIN tasks t
          ON t.user_id IN (ss.requester_id, ss.partner_id)
        WHERE ss.status = 'accepted'
        ON CONFLICT ON CONSTRAINT uq_space_sync_task_invite DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_space_sync_task_invites_to_user_id"),
        table_name="space_sync_task_invites",
    )
    op.drop_index(
        op.f("ix_space_sync_task_invites_task_id"),
        table_name="space_sync_task_invites",
    )
    op.drop_index(
        op.f("ix_space_sync_task_invites_id"),
        table_name="space_sync_task_invites",
    )
    op.drop_table("space_sync_task_invites")
    op.execute("DROP TYPE IF EXISTS spacesynctaskinvitestatus")
