"""Story Comment model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class StoryComment(Base):
    """Story Comment model - комментарии к историям"""
    __tablename__ = "story_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    story = relationship("Story", backref="comments")
    user = relationship("User", backref="story_comments")

    def __repr__(self):
        return f"<StoryComment {self.id} story={self.story_id} user={self.user_id}>"
