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
    
    class Config:
        populate_by_name = True


class MemoryCreate(MemoryBase):
    """Memory creation schema"""
    category_id: Optional[UUID] = None
    memory_metadata: Optional[Dict[str, Any]] = None


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
    image_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    memory_metadata: Dict[str, Any] = {}
    ai_confidence: Optional[float]
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Memory(MemoryInDB):
    """Memory response schema"""
    pass


class MemoryWithCategory(Memory):
    """Memory with category details"""
    category: Optional["Category"] = None


class MemoryList(BaseModel):
    """Paginated memory list"""
    items: List[Memory]
    total: int
    page: int
    size: int
    pages: int


# Import for forward reference
from app.schemas.category import Category
MemoryWithCategory.model_rebuild()

