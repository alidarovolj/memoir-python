"""Subtask Pydantic schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SubtaskBase(BaseModel):
    """Base Subtask schema"""
    title: str = Field(..., min_length=1, max_length=500, description="Subtask title")
    is_completed: bool = Field(default=False, description="Whether subtask is completed")
    order: int = Field(default=0, ge=0, description="Order for sorting (drag & drop)")


class SubtaskCreate(SubtaskBase):
    """Schema for creating a new subtask"""
    pass


class SubtaskUpdate(BaseModel):
    """Schema for updating a subtask"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    is_completed: Optional[bool] = None
    order: Optional[int] = Field(None, ge=0)


class SubtaskInDB(SubtaskBase):
    """Schema for subtask in database"""
    id: UUID
    task_id: UUID
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubtaskReorder(BaseModel):
    """Schema for reordering subtasks"""
    subtask_id: UUID
    new_order: int = Field(..., ge=0)

