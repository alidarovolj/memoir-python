"""add_space_syncs_table

Revision ID: add_space_syncs
Revises: add_messages_table
Create Date: 2026-05-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_space_syncs"
down_revision = "add_messages_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE spacesyncstatus AS ENUM ('pending', 'accepted', 'rejected', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.create_table(
        "space_syncs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "accepted",
                "rejected",
                "cancelled",
                name="spacesyncstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "partner_id", name="uq_space_sync_pair"),
    )
    op.create_index(op.f("ix_space_syncs_id"), "space_syncs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_space_syncs_id"), table_name="space_syncs")
    op.drop_table("space_syncs")

    sync_status = postgresql.ENUM(
        "pending",
        "accepted",
        "rejected",
        "cancelled",
        name="spacesyncstatus",
    )
    sync_status.drop(op.get_bind(), checkfirst=True)
