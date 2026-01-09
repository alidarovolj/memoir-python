"""Pet social schemas"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class GiftType(str, Enum):
    """Types of gifts"""
    TREAT = "treat"
    TOY = "toy"
    HUG = "hug"


class SendGiftRequest(BaseModel):
    """Request to send a gift"""
    to_user_id: str = Field(..., alias="toUserId")
    gift_type: GiftType = Field(..., alias="giftType")
    
    class Config:
        use_enum_values = True
        populate_by_name = True


class PetVillageUserResponse(BaseModel):
    """User's pet in village"""
    user_id: str = Field(..., alias="userId")
    username: str
    pet_name: str = Field(..., alias="petName")
    pet_type: str = Field(..., alias="petType")
    pet_level: int = Field(..., alias="petLevel")
    evolution_stage: str = Field(..., alias="evolutionStage")
    is_shiny: bool = Field(default=False, alias="isShiny")
    
    class Config:
        populate_by_name = True
        by_alias = True


class PetGiftResponse(BaseModel):
    """Gift information"""
    id: str
    from_user_id: str = Field(..., alias="fromUserId")
    from_username: str = Field(..., alias="fromUsername")
    gift_type: GiftType = Field(..., alias="giftType")
    claimed: bool
    sent_at: str = Field(..., alias="sentAt")
    
    class Config:
        use_enum_values = True
        populate_by_name = True
        by_alias = True


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: str = Field(..., alias="userId")
    username: str
    pet_name: str = Field(..., alias="petName")
    pet_type: str = Field(..., alias="petType")
    level: int
    xp: int
    evolution_stage: str = Field(..., alias="evolutionStage")
    is_shiny: bool = Field(default=False, alias="isShiny")
    
    class Config:
        populate_by_name = True
        by_alias = True
