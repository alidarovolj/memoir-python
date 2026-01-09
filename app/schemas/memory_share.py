from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.memory import PrivacyLevel


# ============================================================================
# Request Schemas
# ============================================================================

class ShareMemoryRequest(BaseModel):
    """Request to share memory with specific users"""
    memory_id: UUID
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs to share with")
    can_comment: bool = Field(default=True, description="Allow recipients to comment")
    can_react: bool = Field(default=True, description="Allow recipients to react")


class UpdateMemoryPrivacy(BaseModel):
    """Update memory privacy settings"""
    memory_id: UUID
    privacy_level: PrivacyLevel


class UnshareMemoryRequest(BaseModel):
    """Remove sharing for specific users"""
    memory_id: UUID
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs to unshare with")


# ============================================================================
# Response Schemas
# ============================================================================

class SharedWithUser(BaseModel):
    """User that memory is shared with"""
    user_id: int
    username: str
    can_comment: bool
    can_react: bool
    shared_at: datetime
    viewed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class MemoryShareInfo(BaseModel):
    """Information about memory sharing"""
    memory_id: UUID
    privacy_level: PrivacyLevel
    shared_with: List[SharedWithUser]
    total_shares: int


class SharedMemoryListItem(BaseModel):
    """Shared memory item in list"""
    memory_id: UUID
    title: str
    content: str
    image_url: Optional[str] = None
    created_at: datetime
    
    # Owner info
    owner_id: UUID
    owner_username: str
    
    # Share info
    shared_at: datetime
    can_comment: bool
    can_react: bool
    viewed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class SharedMemoriesList(BaseModel):
    """List of memories shared with current user"""
    memories: List[SharedMemoryListItem]
    total: int


class ShareActionResponse(BaseModel):
    """Response for share/unshare actions"""
    success: bool
    message: str
    memory_id: UUID
    shared_with_count: int
