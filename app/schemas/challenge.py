"""Challenge schemas for API validation"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class ChallengeGoal(BaseModel):
    """Challenge goal configuration"""
    type: str = Field(..., description="Goal type: create_memories, complete_tasks, daily_streak, etc.")
    target: int = Field(..., description="Target number to achieve")
    description: str = Field(..., description="Human-readable goal description")


class GlobalChallengeBase(BaseModel):
    """Base schema for GlobalChallenge"""
    title: str = Field(..., max_length=200)
    description: str
    emoji: str = Field(default="🎯", max_length=10)
    start_date: datetime
    end_date: datetime
    goal: Dict[str, Any]
    is_active: bool = Field(default=True)


class GlobalChallengeCreate(GlobalChallengeBase):
    """Schema for creating a challenge"""
    pass


class GlobalChallengeUpdate(BaseModel):
    """Schema for updating a challenge"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    emoji: Optional[str] = Field(None, max_length=10)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goal: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class GlobalChallenge(GlobalChallengeBase):
    """Full challenge schema with computed fields"""
    id: UUID
    participants_count: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_ongoing: bool = Field(default=False, description="Whether challenge is currently active")
    days_remaining: int = Field(default=0, description="Days until challenge ends")
    
    class Config:
        from_attributes = True


class ChallengeParticipantBase(BaseModel):
    """Base schema for ChallengeParticipant"""
    challenge_id: UUID
    progress: int = Field(default=0, ge=0)
    completed: bool = Field(default=False)


class ChallengeParticipantCreate(BaseModel):
    """Schema for joining a challenge"""
    pass  # challenge_id will come from path param


class ChallengeParticipant(ChallengeParticipantBase):
    """Full participant schema"""
    id: UUID
    user_id: UUID
    joined_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChallengeProgress(BaseModel):
    """User's progress in a specific challenge"""
    challenge_id: UUID
    challenge_title: str
    challenge_emoji: str
    goal: Dict[str, Any]
    progress: int
    target: int
    completed: bool
    percentage: float = Field(description="Progress percentage (0-100)")
    rank: Optional[int] = Field(None, description="User's rank in leaderboard")
    joined_at: datetime


class LeaderboardEntry(BaseModel):
    """Single entry in challenge leaderboard"""
    rank: int
    user_id: UUID
    username: Optional[str]
    avatar_url: Optional[str]
    progress: int
    completed: bool
    percentage: float


class ChallengeLeaderboard(BaseModel):
    """Challenge leaderboard response"""
    challenge_id: UUID
    challenge_title: str
    entries: list[LeaderboardEntry]
    total_participants: int
    user_rank: Optional[int] = Field(None, description="Current user's rank if participating")


class ChallengeList(BaseModel):
    """List of challenges with pagination"""
    items: list[GlobalChallenge]
    total: int
    page: int
    size: int
    pages: int
