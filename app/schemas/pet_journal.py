"""Pet journal schemas"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class JournalEntryType(str, Enum):
    """Types of journal entries"""
    EVOLUTION = "evolution"
    MILESTONE = "milestone"
    PHOTO = "photo"
    ACHIEVEMENT = "achievement"


class CreateJournalEntryRequest(BaseModel):
    """Request to create journal entry"""
    entry_type: JournalEntryType = Field(..., alias="entryType")
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, alias="imageUrl")
    
    class Config:
        use_enum_values = True
        populate_by_name = True


class PetJournalEntryResponse(BaseModel):
    """Journal entry"""
    id: str
    pet_id: str = Field(..., alias="petId")
    entry_type: JournalEntryType = Field(..., alias="entryType")
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, alias="imageUrl")
    level_at_time: Optional[int] = Field(None, alias="levelAtTime")
    evolution_stage_at_time: Optional[str] = Field(None, alias="evolutionStageAtTime")
    created_at: str = Field(..., alias="createdAt")
    
    class Config:
        use_enum_values = True
        populate_by_name = True
        by_alias = True
