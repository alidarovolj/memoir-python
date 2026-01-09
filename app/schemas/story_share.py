"""Story Share Pydantic schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class StoryShareBase(BaseModel):
    """Base story share schema"""
    recipient_id: UUID


class StoryShareCreate(StoryShareBase):
    """Story share creation schema"""
    pass


class StoryShareInDB(BaseModel):
    """Story share in database schema"""
    id: UUID
    story_id: UUID
    sender_id: UUID
    recipient_id: UUID
    created_at: datetime
    viewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StoryShare(StoryShareInDB):
    """Story share response schema"""
    pass


class StoryShareWithDetails(StoryShare):
    """Story share with sender, recipient and story details"""
    sender: dict  # username, avatar_url, first_name, last_name
    recipient: dict  # username, avatar_url, first_name, last_name
    story: Optional[dict] = None  # story details

    model_config = ConfigDict(from_attributes=True)


class StoryShareList(BaseModel):
    """Story share list"""
    items: list[StoryShareWithDetails]
    total: int
