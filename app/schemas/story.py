"""Story Pydantic schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class StoryBase(BaseModel):
    """Base story schema"""
    memory_id: UUID
    is_public: bool = True


class StoryCreate(StoryBase):
    """Story creation schema"""
    pass


class StoryInDB(StoryBase):
    """Story in database schema"""
    id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Story(StoryInDB):
    """Story response schema"""
    pass


class StoryWithDetails(Story):
    """Story with user and memory details"""
    user: Optional[dict] = None  # username, avatar
    memory: Optional[dict] = None  # title, image_url, content preview

    model_config = ConfigDict(from_attributes=True)


class StoryList(BaseModel):
    """Story list"""
    items: list[StoryWithDetails]
    total: int

