"""Story model"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Story(Base):
    """Story model - публичные воспоминания в формате историй"""
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_public = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7), nullable=False)  # Истории живут 7 дней

    # Relationships
    user = relationship("User", backref="stories")
    memory = relationship("Memory", backref="stories")

    def __repr__(self):
        return f"<Story {self.id} by {self.user_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Проверка, истекла ли история"""
        return datetime.utcnow() > self.expires_at

