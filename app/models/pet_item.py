"""Pet item models - Accessories and customization items"""
from sqlalchemy import Column, String, Integer, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class ItemType(str, enum.Enum):
    """Types of pet items"""
    HAT = "hat"
    GLASSES = "glasses"
    CLOTHING = "clothing"
    BACKGROUND = "background"
    EFFECT = "effect"


class ItemRarity(str, enum.Enum):
    """Item rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class PetItem(Base):
    """
    Available pet items (shop catalog)
    """
    __tablename__ = "pet_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Item info
    item_type = Column(SQLEnum(ItemType), nullable=False)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), nullable=False)
    description = Column(String(500))
    
    # Cost and rarity
    cost_xp = Column(Integer, nullable=False, default=100)
    rarity = Column(SQLEnum(ItemRarity), nullable=False, default=ItemRarity.COMMON)
    
    # Unlock requirements (JSON)
    unlock_requirement = Column(JSON, default={})  # {level: 10, achievement: "xyz"}
    
    # Metadata
    created_at = Column(String(100), server_default=func.now())
    
    def __repr__(self):
        return f"<PetItem {self.name} ({self.item_type}, {self.rarity})>"


class UserPetItem(Base):
    """
    User's owned pet items
    """
    __tablename__ = "user_pet_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("pet_items.id"), nullable=False)
    
    # Status
    equipped = Column(Boolean, default=False, nullable=False)
    purchased_at = Column(String(100), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    item = relationship("PetItem")
    
    def __repr__(self):
        return f"<UserPetItem user={self.user_id}, item={self.item_id}, equipped={self.equipped}>"
