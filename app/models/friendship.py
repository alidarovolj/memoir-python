from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class FriendshipStatus(str, enum.Enum):
    """Friendship request status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class Friendship(Base):
    """
    Friendship model - represents relationship between two users
    
    Note: Each friendship is stored as a single record where:
    - requester_id: user who sent the friend request
    - addressee_id: user who received the friend request
    
    To get all friends of a user, query where:
    (requester_id = user_id OR addressee_id = user_id) AND status = 'accepted'
    """
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    
    # Requester: user who initiated the friend request
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Addressee: user who received the friend request
    addressee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Friendship status
    status = Column(
        Enum(FriendshipStatus, native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=FriendshipStatus.PENDING,
        server_default="pending"
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], backref="sent_requests")
    addressee = relationship("User", foreign_keys=[addressee_id], backref="received_requests")
    
    # Constraints
    __table_args__ = (
        # Ensure that there's only one friendship record between two users
        UniqueConstraint('requester_id', 'addressee_id', name='uq_friendship_pair'),
        # Ensure user can't befriend themselves
        # This is handled in application logic
    )
    
    def __repr__(self):
        return f"<Friendship {self.requester_id} -> {self.addressee_id} ({self.status})>"
