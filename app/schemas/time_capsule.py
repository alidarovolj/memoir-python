"""Time Capsule schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class TimeCapsuleBase(BaseModel):
    """Base time capsule schema"""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the capsule")
    content: str = Field(..., min_length=1, description="Message to future self")
    open_date: datetime = Field(..., description="When capsule can be opened")


class TimeCapsuleCreate(TimeCapsuleBase):
    """Schema for creating a time capsule"""
    pass


class TimeCapsuleUpdate(BaseModel):
    """Schema for updating a time capsule (only before it's opened)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    open_date: Optional[datetime] = None


class TimeCapsule(TimeCapsuleBase):
    """Full time capsule schema"""
    id: UUID
    user_id: UUID
    created_at: datetime
    opened_at: Optional[datetime] = None
    status: str
    notification_sent: bool
    is_ready_to_open: bool
    days_until_open: int
    
    model_config = ConfigDict(from_attributes=True)


class TimeCapsuleList(BaseModel):
    """List of time capsules with pagination"""
    items: list[TimeCapsule]
    total: int
    page: int
    pages: int
