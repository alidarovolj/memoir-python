"""Pydantic schemas for Task Group"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TaskGroupBase(BaseModel):
    """Base Task Group schema"""
    name: str = Field(..., max_length=100)
    color: str = Field(..., max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")  # HEX color
    icon: str = Field(..., max_length=100)
    notification_enabled: str = Field("none", max_length=20)  # none, automatic, custom
    order_index: int = Field(0, ge=0)


class TaskGroupCreate(TaskGroupBase):
    """Schema for creating a task group"""
    pass


class TaskGroupUpdate(BaseModel):
    """Schema for updating a task group"""
    name: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=100)
    notification_enabled: Optional[str] = Field(None, max_length=20)
    order_index: Optional[int] = Field(None, ge=0)


class TaskGroup(TaskGroupBase):
    """Task Group schema for API responses"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskGroupListResponse(BaseModel):
    """Schema for task group list response"""
    items: list[TaskGroup]
    total: int
