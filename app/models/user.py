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
    phone_number = Column(String(20), unique=True, nullable=True, index=True)  # Now optional for Google auth
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)  # Google OAuth ID
    apple_id = Column(String(255), unique=True, nullable=True, index=True)  # Apple OAuth ID
    username = Column(String(100), unique=True, nullable=True, index=True)
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Keep email optional for future OAuth support
    email = Column(String(255), unique=True, nullable=True, index=True)
    
    # Push Notifications Settings
    fcm_token = Column(String(255), nullable=True)  # Firebase Cloud Messaging token
    task_reminders_enabled = Column(Boolean, default=True, nullable=False)
    reminder_hours_before = Column(Integer, default=1, nullable=False)  # Напоминать за N часов до due_date
    
    # Personal data fields
    profession = Column(String(200), nullable=True)
    telegram_url = Column(String(500), nullable=True)
    whatsapp_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    about_me = Column(String(2000), nullable=True)  # Text about user
    city = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    education = Column(String(200), nullable=True)
    hobbies = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    task_groups = relationship("TaskGroup", back_populates="user", cascade="all, delete-orphan")
    pet = relationship("Pet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    time_capsules = relationship("TimeCapsule", back_populates="user", cascade="all, delete-orphan")
    challenge_participations = relationship("ChallengeParticipant", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.phone_number}>"
    
    @property
    def has_pet(self) -> bool:
        """Check if user has a pet"""
        return self.pet is not None

