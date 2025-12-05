"""Task model for planning and task management"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class TaskStatus(str, enum.Enum):
    """Task status enum"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enum"""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TimeScope(str, enum.Enum):
    """Task time scope enum"""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    long_term = "long_term"


class Task(Base):
    """Task model - represents user's tasks and plans"""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Timing
    due_date = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(String(5), nullable=True)  # Format: "HH:MM" (e.g. "08:00")
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.pending, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.medium, nullable=False)
    time_scope = Column(SQLEnum(TimeScope), default=TimeScope.daily, nullable=False)

    # Relations
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    related_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"), nullable=True)

    # AI
    ai_suggested = Column(Boolean, default=False, nullable=False)
    ai_confidence = Column(Float, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # Recurring
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_rule = Column(String(100), nullable=True)  # RRULE format (RFC 5545)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)  # For recurring instances

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category")
    related_memory = relationship("Memory", foreign_keys="[Task.related_memory_id]")
    parent_task = relationship("Task", remote_side="[Task.id]", foreign_keys="[Task.parent_task_id]", backref="recurring_instances")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan", order_by="Subtask.order")

    def __repr__(self):
        return f"<Task {self.id} - {self.title} ({self.status})>"

