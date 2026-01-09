"""Pydantic schemas for Task"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskPriority, TimeScope

if TYPE_CHECKING:
    from app.schemas.subtask import SubtaskInDB


class TaskBase(BaseModel):
    """Base Task schema"""
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color format
    icon: Optional[str] = Field(None, max_length=50)  # Icon name
    due_date: Optional[datetime] = None
    scheduled_time: Optional[str] = Field(None, max_length=5, pattern=r"^\d{2}:\d{2}$")  # Format: "HH:MM"
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    time_scope: TimeScope = TimeScope.daily
    category_id: Optional[UUID] = None
    task_group_id: Optional[UUID] = None
    related_memory_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # RRULE format (RFC 5545)
    parent_task_id: Optional[UUID] = None  # For recurring instances


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color format
    icon: Optional[str] = Field(None, max_length=50)  # Icon name
    due_date: Optional[datetime] = None
    scheduled_time: Optional[str] = Field(None, max_length=5, pattern=r"^\d{2}:\d{2}$")
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    time_scope: Optional[TimeScope] = None
    category_id: Optional[UUID] = None
    task_group_id: Optional[UUID] = None
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
    task_group_name: Optional[str] = None
    task_group_icon: Optional[str] = None
    subtasks: List["SubtaskInDB"] = []

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


class TaskAnalyzeResponse(BaseModel):
    """Schema for AI task analysis response"""
    time_scope: TimeScope
    priority: TaskPriority
    suggested_time: Optional[str] = None  # Format: "HH:MM"
    suggested_due_date: Optional[str] = None  # "today", "tomorrow", "this_week", "this_month"
    needs_deadline: bool = False
    is_recurring: bool = False  # Should this task repeat?
    category: Optional[str] = None
    confidence: float
    reasoning: str


class TaskToMemoryConversion(BaseModel):
    """Schema for converting a completed task to a memory"""
    content: Optional[str] = None  # Additional content/notes
    rating: Optional[float] = Field(None, ge=0, le=10)  # Rating for movies/books (0-10)
    notes: Optional[str] = None  # Additional notes/thoughts
    image_url: Optional[str] = None  # Optional image
    backdrop_url: Optional[str] = None  # Optional backdrop


# Resolve forward references
from app.schemas.subtask import SubtaskInDB  # noqa: E402
Task.model_rebuild()

