"""Time Capsule model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class CapsuleStatus(str, enum.Enum):
    """Status of time capsule"""
    SEALED = "SEALED"      # Капсула запечатана, ждет открытия
    OPENED = "OPENED"      # Капсула открыта
    EXPIRED = "EXPIRED"    # Дата прошла, но не открыта


class TimeCapsule(Base):
    """
    Time Capsule - письмо будущему себе
    Пользователь создает капсулу с сообщением, которое откроется в будущем
    """
    __tablename__ = "time_capsules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    open_date = Column(DateTime(timezone=True), nullable=False)  # Когда можно открыть
    opened_at = Column(DateTime(timezone=True), nullable=True)   # Когда была открыта
    
    # Status
    status = Column(SQLEnum(CapsuleStatus), default=CapsuleStatus.SEALED, nullable=False)
    
    # Notifications
    notification_sent = Column(Boolean, default=False, nullable=False)  # Push отправлен?
    
    # Relationships
    user = relationship("User", back_populates="time_capsules")

    def __repr__(self):
        return f"<TimeCapsule {self.id} - {self.title}>"
    
    @property
    def is_ready_to_open(self) -> bool:
        """Check if capsule can be opened"""
        now = datetime.now(timezone.utc)
        return self.open_date <= now and self.status == CapsuleStatus.SEALED
    
    @property
    def days_until_open(self) -> int:
        """Days until capsule can be opened"""
        if self.status != CapsuleStatus.SEALED:
            return 0
        now = datetime.now(timezone.utc)
        delta = self.open_date - now
        return max(0, delta.days)
