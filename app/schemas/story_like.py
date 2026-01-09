"""Story Like Pydantic schemas"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class StoryLikeBase(BaseModel):
    """Base story like schema"""
    pass


class StoryLikeCreate(StoryLikeBase):
    """Story like creation schema"""
    pass


class StoryLikeInDB(StoryLikeBase):
    """Story like in database schema"""
    id: UUID
    story_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StoryLike(StoryLikeInDB):
    """Story like response schema"""
    pass


class StoryLikeWithUser(StoryLike):
    """Story like with user details"""
    user: dict  # username, avatar_url, first_name, last_name

    model_config = ConfigDict(from_attributes=True)
