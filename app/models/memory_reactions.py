from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class ReactionType(str, enum.Enum):
    """Reaction types for memories"""
    LIKE = "like"  # ❤️
    LOVE = "love"  # 😍
    FIRE = "fire"  # 🔥
    STAR = "star"  # ⭐
    CELEBRATE = "celebrate"  # 🎉
    THINKING = "thinking"  # 🤔


class MemoryReaction(Base):
    """
    User reactions to memories (likes, hearts, etc.)
    """
    __tablename__ = "memory_reactions"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    reaction_type = Column(
        Enum(ReactionType),
        nullable=False,
        default=ReactionType.LIKE
    )
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    memory = relationship("Memory", backref="reactions")
    user = relationship("User", backref="memory_reactions")
    
    def __repr__(self):
        return f"<MemoryReaction {self.user_id} -> {self.memory_id} ({self.reaction_type})>"


class MemoryComment(Base):
    """
    Comments on memories with threading support
    """
    __tablename__ = "memory_comments"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Comment content
    text = Column(Text, nullable=False)
    
    # Threading support (optional parent comment for replies)
    parent_id = Column(Integer, ForeignKey("memory_comments.id", ondelete="CASCADE"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    memory = relationship("Memory", backref="comments")
    user = relationship("User", backref="memory_comments")
    
    # Self-referential relationship for threading
    parent = relationship("MemoryComment", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<MemoryComment {self.id} by {self.user_id}>"
