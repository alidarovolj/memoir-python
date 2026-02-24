"""Memory Pydantic schemas"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MemoryBase(BaseModel):
    """Base memory schema"""
    title: str = Field(..., max_length=500)
    content: str
    source_type: str = "text"
    source_url: Optional[str] = None
    image_url: Optional[str] = None  # For posters/covers
    backdrop_url: Optional[str] = None  # For backdrop images
    audio_url: Optional[str] = None  # For voice notes
    audio_transcript: Optional[str] = None  # Whisper transcription
    
    class Config:
        populate_by_name = True


class MemoryCreate(MemoryBase):
    """Memory creation schema"""
    category_id: Optional[UUID] = None
    memory_metadata: Optional[Dict[str, Any]] = None
    related_task_id: Optional[UUID] = None  # Привязка к задаче, если воспоминание создано из задачи
    privacy_level: Optional[str] = None  # private, friends_only, shared, public. Default: friends_only


class MemoryUpdate(BaseModel):
    """Memory update schema"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    category_id: Optional[UUID] = None
    source_url: Optional[str] = None
    tags: Optional[List[str]] = None
    memory_metadata: Optional[Dict[str, Any]] = None


class MemoryInDB(MemoryBase):
    """Memory in database schema"""
    id: UUID
    user_id: UUID
    category_id: Optional[UUID]
    related_task_id: Optional[UUID] = None
    image_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    audio_url: Optional[str] = None
    audio_transcript: Optional[str] = None
    memory_metadata: Dict[str, Any] = {}
    ai_confidence: Optional[float]
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Memory(MemoryInDB):
    """Memory response schema"""
    category_name: Optional[str] = None


class MemoryWithCategory(Memory):
    """Memory with category details"""
    category: Optional["Category"] = None


class MemoryFeedItem(Memory):
    """Memory item for the feed — includes author info and engagement stats."""
    owner_id: Optional[str] = None
    owner_username: Optional[str] = None
    owner_first_name: Optional[str] = None
    owner_last_name: Optional[str] = None
    owner_avatar_url: Optional[str] = None
    is_own: bool = True
    is_friend: bool = False
    reactions_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    is_reacted: bool = False


class MemoryList(BaseModel):
    """Paginated memory list"""
    items: List[Memory]
    total: int
    page: int
    size: int
    pages: int


class MemoryFeedList(BaseModel):
    """Paginated feed list with author info"""
    items: List[MemoryFeedItem]
    total: int
    page: int
    size: int
    pages: int


# Import for forward reference
from app.schemas.category import Category
MemoryWithCategory.model_rebuild()

