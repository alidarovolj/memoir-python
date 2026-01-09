"""Memory model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class SourceType(str, enum.Enum):
    """Source type enum"""
    text = "text"
    link = "link"
    image = "image"
    voice = "voice"


class PrivacyLevel(str, enum.Enum):
    """Privacy level for memories"""
    PRIVATE = "private"  # Only owner
    FRIENDS_ONLY = "friends_only"  # All friends
    SHARED = "shared"  # Specific users
    PUBLIC = "public"  # Everyone


class Memory(Base):
    """Memory model"""
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)  # Link to task if created from task
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(SQLEnum(SourceType, native_enum=True, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=SourceType.text)
    source_url = Column(String(2048), nullable=True)
    image_url = Column(String(2048), nullable=True)  # For posters/covers
    backdrop_url = Column(String(2048), nullable=True)  # For backdrop images
    audio_url = Column(String(2048), nullable=True)  # For voice notes
    audio_transcript = Column(Text, nullable=True)  # Whisper transcription
    
    # Privacy settings
    privacy_level = Column(
        SQLEnum(PrivacyLevel, native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PrivacyLevel.PRIVATE,
        server_default="private"
    )
    
    # AI-generated fields
    memory_metadata = Column(JSONB, nullable=True, default=dict)
    ai_confidence = Column(Float, nullable=True)
    tags = Column(ARRAY(String), nullable=True, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="memories")
    category = relationship("Category", back_populates="memories")
    related_task = relationship("Task", foreign_keys="[Memory.related_task_id]")
    embedding = relationship("Embedding", back_populates="memory", uselist=False, cascade="all, delete-orphan")
    
    # Many-to-many relationship with users (for sharing)
    shared_with = relationship(
        "User",
        secondary="memory_shares",
        backref="shared_memories_received"
    )

    def __repr__(self):
        return f"<Memory {self.title[:30]}>"

