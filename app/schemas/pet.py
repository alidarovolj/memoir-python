"""Pet schemas for API requests and responses"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class PetType(str, Enum):
    """Available pet types"""
    BIRD = "BIRD"
    CAT = "CAT"
    DRAGON = "DRAGON"
    FOX = "FOX"          # Лиса - хитрая и умная
    PANDA = "PANDA"      # Панда - милая и ленивая
    UNICORN = "UNICORN"  # Единорог - магический и редкий
    RABBIT = "RABBIT"    # Кролик - быстрый и энергичный
    OWL = "OWL"          # Сова - мудрая и ночная


class EvolutionStage(str, Enum):
    """Pet evolution stages"""
    EGG = "EGG"      # 0-4 levels
    BABY = "BABY"    # 5-14 levels
    CHILD = "CHILD"  # 15-24 levels (НОВАЯ СТАДИЯ)
    ADULT = "ADULT"  # 25-39 levels
    LEGEND = "LEGEND"  # 40+ levels


class PetCreate(BaseModel):
    """Schema for creating a new pet"""
    pet_type: PetType = Field(..., description="Type of pet to create", alias="petType")
    name: str = Field(..., min_length=1, max_length=50, description="Pet name chosen by user")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Pet name cannot be empty')
        return v.strip()
    
    class Config:
        use_enum_values = True
        populate_by_name = True  # Allow both pet_type and petType


class PetStats(BaseModel):
    """Pet statistics"""
    level: int
    xp: int
    xp_for_next_level: int = Field(..., alias="xpForNextLevel")
    evolution_stage: EvolutionStage = Field(..., alias="evolutionStage")
    happiness: int = Field(..., ge=0, le=100)
    health: int = Field(..., ge=0, le=100)
    
    class Config:
        use_enum_values = True
        populate_by_name = True
        by_alias = True


class PetResponse(BaseModel):
    """Full pet information"""
    id: str
    user_id: str = Field(..., alias="userId")
    pet_type: PetType = Field(..., alias="petType")
    name: str
    level: int
    xp: int
    xp_for_next_level: int = Field(..., alias="xpForNextLevel")
    evolution_stage: EvolutionStage = Field(..., alias="evolutionStage")
    happiness: int
    health: int
    last_fed: datetime = Field(..., alias="lastFed")
    last_played: datetime = Field(..., alias="lastPlayed")
    created_at: datetime = Field(..., alias="createdAt")
    accessories: str
    
    # New Pet 2.0 fields
    is_shiny: bool = Field(default=False, alias="isShiny")
    mutation_type: Optional[str] = Field(None, alias="mutationType")
    special_effect: Optional[str] = Field(None, alias="specialEffect")
    
    # Emotions (Pet 2.0.5)
    current_emotion: Optional[str] = Field(None, alias="currentEmotion")
    speech_bubble: Optional[str] = Field(None, alias="speechBubble")
    
    # Computed fields
    needs_attention: bool = Field(
        default=False, 
        description="True if happiness or health < 30",
        alias="needsAttention"
    )
    can_evolve: bool = Field(
        default=False,
        description="True if pet is ready to evolve",
        alias="canEvolve"
    )
    
    class Config:
        orm_mode = True
        use_enum_values = True
        populate_by_name = True
        by_alias = True  # Use aliases when serializing
    
    @validator('needs_attention', always=True)
    def check_needs_attention(cls, v, values):
        return values.get('happiness', 100) < 30 or values.get('health', 100) < 30
    
    @validator('xp_for_next_level', always=True)
    def calculate_xp_for_next_level(cls, v, values):
        level = values.get('level', 1)
        return 100 + (level * 50)


class PetActionResponse(BaseModel):
    """Response after pet action (feed/play)"""
    message: str
    pet: PetResponse
    level_ups: int = 0
    evolved: bool = False
    rewards: Optional[dict] = None
    
    class Config:
        use_enum_values = True


class PetUpdateName(BaseModel):
    """Schema for updating pet name"""
    name: str = Field(..., min_length=1, max_length=50)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Pet name cannot be empty')
        return v.strip()
