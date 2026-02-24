"""SubtaskCompletion model for tracking per-instance subtask completion in recurring tasks"""
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class SubtaskCompletion(Base):
    """
    Tracks subtask completion per task instance (day) for recurring habits.

    For recurring tasks, subtasks belong to the parent task, but completion
    status must be per instance (per day). This table stores:
    - task_id: the instance (recurring day) ID
    - subtask_id: the parent's subtask ID
    - completed_at: when it was completed for this instance
    """
    __tablename__ = "subtask_completions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey("subtasks.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)

    task = relationship("Task", backref="subtask_completions")
    subtask = relationship("Subtask", backref="completions")

    def __repr__(self):
        return f"<SubtaskCompletion task={self.task_id} subtask={self.subtask_id}>"
