from datetime import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SpaceSyncStatus(str, enum.Enum):
    """Space synchronization request status between two friends."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SpaceSync(Base):
    """
    Task space sync link between two users.

    requester_id sends a sync request to partner_id.
    When accepted, both users can view each other's tasks.
    """

    __tablename__ = "space_syncs"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    partner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum(
            SpaceSyncStatus,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SpaceSyncStatus.PENDING,
        server_default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    requester = relationship("User", foreign_keys=[requester_id], backref="sent_space_syncs")
    partner = relationship("User", foreign_keys=[partner_id], backref="received_space_syncs")

    __table_args__ = (
        UniqueConstraint("requester_id", "partner_id", name="uq_space_sync_pair"),
    )

    def __repr__(self) -> str:
        return f"<SpaceSync {self.requester_id} -> {self.partner_id} ({self.status})>"
