"""Achievement schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class AchievementBase(BaseModel):
    """Base achievement schema"""
    code: str
    title: str
    description: str
    emoji: str
    achievement_type: str
    criteria_count: int
    xp_reward: int


class Achievement(AchievementBase):
    """Full achievement schema"""
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserAchievementProgress(BaseModel):
    """User's progress on an achievement"""
    achievement_id: UUID
    achievement_code: str
    title: str
    description: str
    emoji: str
    achievement_type: str
    criteria_count: int
    progress: int
    unlocked: bool
    unlocked_at: Optional[datetime]
    percentage: float
    xp_reward: int


class AchievementList(BaseModel):
    """List of user achievements"""
    unlocked: list[UserAchievementProgress]
    in_progress: list[UserAchievementProgress]
    locked: list[UserAchievementProgress]
