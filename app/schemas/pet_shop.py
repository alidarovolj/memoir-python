"""Pet shop schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ItemType(str, Enum):
    """Types of pet items"""
    HAT = "hat"
    GLASSES = "glasses"
    CLOTHING = "clothing"
    BACKGROUND = "background"
    EFFECT = "effect"


class ItemRarity(str, Enum):
    """Item rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class PetItemResponse(BaseModel):
    """Pet item in shop"""
    id: str
    item_type: ItemType = Field(..., alias="itemType")
    name: str
    emoji: str
    description: Optional[str] = None
    cost_xp: int = Field(..., alias="costXp")
    rarity: ItemRarity
    unlock_requirement: Dict[str, Any] = Field(default_factory=dict, alias="unlockRequirement")
    is_unlocked: bool = Field(default=True, alias="isUnlocked")
    is_owned: bool = Field(default=False, alias="isOwned")
    is_equipped: bool = Field(default=False, alias="isEquipped")
    
    class Config:
        use_enum_values = True
        populate_by_name = True
        by_alias = True


class UserPetItemResponse(BaseModel):
    """User's owned pet item"""
    id: str
    user_id: str = Field(..., alias="userId")
    item_id: str = Field(..., alias="itemId")
    equipped: bool
    purchased_at: str = Field(..., alias="purchasedAt")
    item: PetItemResponse
    
    class Config:
        orm_mode = True
        populate_by_name = True
        by_alias = True


class PurchaseItemRequest(BaseModel):
    """Request to purchase an item"""
    item_id: str = Field(..., alias="itemId")
    
    class Config:
        populate_by_name = True


class EquipItemRequest(BaseModel):
    """Request to equip/unequip an item"""
    item_id: str = Field(..., alias="itemId")
    equipped: bool
    
    class Config:
        populate_by_name = True
