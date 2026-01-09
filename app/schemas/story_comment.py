"""Story Comment Pydantic schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class StoryCommentBase(BaseModel):
    """Base story comment schema"""
    content: str = Field(..., min_length=1, max_length=5000)


class StoryCommentCreate(StoryCommentBase):
    """Story comment creation schema"""
    pass


class StoryCommentUpdate(BaseModel):
    """Story comment update schema"""
    content: str = Field(..., min_length=1, max_length=5000)


class StoryCommentInDB(StoryCommentBase):
    """Story comment in database schema"""
    id: UUID
    story_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StoryComment(StoryCommentInDB):
    """Story comment response schema"""
    pass


class StoryCommentWithUser(StoryComment):
    """Story comment with user details"""
    user: dict  # username, avatar_url, first_name, last_name

    model_config = ConfigDict(from_attributes=True)


class StoryCommentList(BaseModel):
    """Story comment list"""
    items: list[StoryCommentWithUser]
    total: int
