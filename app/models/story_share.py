"""Story Share model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class StoryShare(Base):
    """Story Share model - отправка историй другим пользователям"""
    __tablename__ = "story_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    viewed_at = Column(DateTime, nullable=True)  # Когда получатель просмотрел

    # Relationships
    story = relationship("Story", backref="shares")
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_stories")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_stories")

    def __repr__(self):
        return f"<StoryShare {self.id} story={self.story_id} from={self.sender_id} to={self.recipient_id}>"

    @property
    def is_viewed(self) -> bool:
        """Проверка, просмотрена ли отправленная история"""
        return self.viewed_at is not None
