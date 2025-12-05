"""Subtask database model"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Subtask(Base):
    """
    Subtask model for breaking down tasks into smaller steps
    
    Example:
        Task: "Подготовить презентацию"
        Subtasks:
            - [x] Собрать материалы
            - [x] Создать структуру
            - [ ] Сделать слайды
            - [ ] Репетиция
    """
    __tablename__ = "subtasks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    
    # Core Fields
    title = Column(String(500), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    order = Column(Integer, nullable=False, default=0)  # For drag & drop ordering
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="subtasks")
    
    def __repr__(self):
        status = "✓" if self.is_completed else "○"
        return f"<Subtask {status} {self.title[:30]}>"

