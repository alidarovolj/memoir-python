"""User model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    
    # Keep email optional for future OAuth support
    email = Column(String(255), unique=True, nullable=True, index=True)
    
    # Push Notifications Settings
    fcm_token = Column(String(255), nullable=True)  # Firebase Cloud Messaging token
    task_reminders_enabled = Column(Boolean, default=True, nullable=False)
    reminder_hours_before = Column(Integer, default=1, nullable=False)  # Напоминать за N часов до due_date
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.phone_number}>"

