"""Task Group model for organizing tasks"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaskGroup(Base):
    """Task Group model - for organizing tasks into groups"""
    __tablename__ = "task_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Basic info
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=False)  # HEX color
    icon = Column(String(100), nullable=False)
    
    # Settings
    notification_enabled = Column(String(20), default="none", nullable=False)  # none, automatic, custom
    order_index = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="task_groups")
    tasks = relationship("Task", back_populates="task_group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TaskGroup {self.id} - {self.name}>"
