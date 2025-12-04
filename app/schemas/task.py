"""Pydantic schemas for Task"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskPriority, TimeScope


class TaskBase(BaseModel):
    """Base Task schema"""
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    time_scope: TimeScope = TimeScope.daily
    category_id: Optional[UUID] = None
    related_memory_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    time_scope: Optional[TimeScope] = None
    category_id: Optional[UUID] = None
    related_memory_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


class TaskInDB(TaskBase):
    """Task schema as stored in database"""
    id: UUID
    user_id: UUID
    completed_at: Optional[datetime] = None
    ai_suggested: bool = False
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Task(TaskInDB):
    """Task schema for API responses"""
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class TaskSuggestion(BaseModel):
    """Schema for AI task suggestions"""
    title: str
    description: Optional[str] = None
    time_scope: TimeScope
    priority: TaskPriority
    confidence: float
    category: Optional[str] = None
    reasoning: Optional[str] = None


class TaskListResponse(BaseModel):
    """Schema for paginated task list response"""
    items: List[Task]
    total: int
    page: int = 1
    page_size: int = 50

