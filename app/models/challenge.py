"""Challenge models for global events and community engagement"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class GlobalChallenge(Base):
    """Global challenges for community engagement"""
    __tablename__ = "global_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    emoji = Column(String(10), nullable=False, default="🎯")
    
    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Goal configuration (JSON)
    # Example: {"type": "create_memories", "target": 30, "description": "Создать 30 воспоминаний"}
    goal = Column(JSON, nullable=False)
    
    # Stats
    participants_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    participants = relationship("ChallengeParticipant", back_populates="challenge", cascade="all, delete-orphan")


class ChallengeParticipant(Base):
    """User participation in challenges"""
    __tablename__ = "challenge_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("global_challenges.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Progress tracking
    progress = Column(Integer, default=0, nullable=False)  # Current progress (e.g., 15 out of 30)
    completed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    challenge = relationship("GlobalChallenge", back_populates="participants")
    user = relationship("User", back_populates="challenge_participations")
