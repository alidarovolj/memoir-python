"""Achievement models for gamification"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class AchievementType(str, enum.Enum):
    """Achievement categories"""
    MEMORIES = "MEMORIES"  # Related to creating memories
    TASKS = "TASKS"  # Related to completing tasks
    STREAKS = "STREAKS"  # Related to daily streaks
    SOCIAL = "SOCIAL"  # Related to sharing/challenges
    PET = "PET"  # Related to pet care
    SPECIAL = "SPECIAL"  # Special events


class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    emoji = Column(String(10), nullable=False, default="🏆")
    
    # Achievement type and criteria
    achievement_type = Column(SQLEnum(AchievementType), nullable=False)
    criteria_count = Column(Integer, nullable=False)  # e.g., 10 memories, 7 day streak
    
    # Rewards
    xp_reward = Column(Integer, default=50, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    """User's unlocked achievements"""
    __tablename__ = "user_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    
    # Progress tracking
    progress = Column(Integer, default=0, nullable=False)  # Current progress towards goal
    unlocked = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
