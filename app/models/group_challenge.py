from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Table
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


# Association table for group challenge members
group_challenge_members = Table(
    'group_challenge_members',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('challenge_id', Integer, ForeignKey('group_challenges.id', ondelete='CASCADE'), nullable=False),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('joined_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('progress', Integer, default=0, nullable=False),  # User's progress
    Column('completed', Boolean, default=False, nullable=False),
)


class GroupChallenge(Base):
    """
    Group challenges that users can complete together
    """
    __tablename__ = "group_challenges"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Challenge details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    goal = Column(Integer, nullable=False)  # Target number (e.g., 30 memories)
    goal_type = Column(String(50), nullable=False)  # Type: 'memories', 'tasks', 'streak'
    
    # Timing
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Settings
    max_members = Column(Integer, default=10, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Challenge metadata stored as JSON
    extra_data = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], backref="created_challenges")
    members = relationship("User", secondary=group_challenge_members, backref="group_challenges")
    
    def __repr__(self):
        return f"<GroupChallenge {self.title}>"


class GroupChallengeInvite(Base):
    """
    Invitations to join group challenges
    """
    __tablename__ = "group_challenge_invites"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("group_challenges.id", ondelete="CASCADE"), nullable=False)
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Status: pending, accepted, declined
    status = Column(String(20), default="pending", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    
    # Relationships
    challenge = relationship("GroupChallenge", backref="invites")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])
    
    def __repr__(self):
        return f"<GroupChallengeInvite challenge={self.challenge_id} invitee={self.invitee_id}>"
