from datetime import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SpaceSyncTaskInviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SpaceSyncTaskInvite(Base):
    """Per-task share invite from a sync partner."""

    __tablename__ = "space_sync_task_invites"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(
            SpaceSyncTaskInviteStatus,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SpaceSyncTaskInviteStatus.PENDING,
        server_default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    task = relationship("Task", backref="space_sync_invites")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])

    __table_args__ = (
        UniqueConstraint("task_id", "to_user_id", name="uq_space_sync_task_invite"),
    )

    def __repr__(self) -> str:
        return (
            f"<SpaceSyncTaskInvite task={self.task_id} "
            f"{self.from_user_id}->{self.to_user_id} ({self.status})>"
        )
