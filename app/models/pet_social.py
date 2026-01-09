"""Pet social features models"""
from sqlalchemy import Column, String, Integer, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class GiftType(str, enum.Enum):
    """Types of gifts to send"""
    TREAT = "treat"
    TOY = "toy"
    HUG = "hug"


class PetVisit(Base):
    """
    Record of pet village visits
    """
    __tablename__ = "pet_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visitor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    visited_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    gift_given = Column(Boolean, default=False, nullable=False)
    visited_at = Column(String(100), server_default=func.now())
    
    # Relationships
    visitor = relationship("User", foreign_keys=[visitor_id])
    visited = relationship("User", foreign_keys=[visited_id])
    
    def __repr__(self):
        return f"<PetVisit from={self.visitor_id} to={self.visited_id}>"


class PetGift(Base):
    """
    Gifts sent between users' pets
    """
    __tablename__ = "pet_gifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    gift_type = Column(SQLEnum(GiftType), nullable=False)
    claimed = Column(Boolean, default=False, nullable=False)
    sent_at = Column(String(100), server_default=func.now())
    claimed_at = Column(String(100), nullable=True)
    
    # Relationships
    sender = relationship("User", foreign_keys=[from_user_id])
    recipient = relationship("User", foreign_keys=[to_user_id])
    
    def __repr__(self):
        return f"<PetGift {self.gift_type} from={self.from_user_id} to={self.to_user_id}>"
