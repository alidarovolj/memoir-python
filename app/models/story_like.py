"""Story Like model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class StoryLike(Base):
    """Story Like model - лайки для историй"""
    __tablename__ = "story_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    story = relationship("Story", backref="likes")
    user = relationship("User", backref="story_likes")

    # Unique constraint: один пользователь может лайкнуть историю только один раз
    __table_args__ = (
        UniqueConstraint('story_id', 'user_id', name='uq_story_like_user'),
    )

    def __repr__(self):
        return f"<StoryLike {self.id} story={self.story_id} user={self.user_id}>"
