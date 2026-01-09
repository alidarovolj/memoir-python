from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from app.models.friendship import FriendshipStatus


# ============================================================================
# Base Schemas
# ============================================================================

class FriendshipBase(BaseModel):
    """Base friendship schema"""
    pass


class FriendProfile(BaseModel):
    """Friend's public profile information"""
    id: int
    username: str
    avatar_url: Optional[str] = None
    created_at: datetime
    
    # Stats (optional, можно добавить позже)
    memories_count: Optional[int] = 0
    friends_count: Optional[int] = 0
    streak_days: Optional[int] = 0
    
    class Config:
        orm_mode = True


# ============================================================================
# Request Schemas
# ============================================================================

class FriendRequestCreate(BaseModel):
    """Send friend request"""
    addressee_id: int = Field(..., description="ID of user to befriend", gt=0)
    
    @validator('addressee_id')
    def validate_addressee(cls, v):
        if v <= 0:
            raise ValueError('addressee_id must be positive')
        return v


class FriendRequestResponse(BaseModel):
    """Respond to friend request"""
    request_id: int = Field(..., description="ID of friendship request")
    action: str = Field(..., description="Action: 'accept' or 'reject'")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['accept', 'reject']:
            raise ValueError('action must be "accept" or "reject"')
        return v


class FriendRemove(BaseModel):
    """Remove friend"""
    friend_id: int = Field(..., description="ID of friend to remove")


class UserSearch(BaseModel):
    """User search request"""
    query: str = Field(..., min_length=1, max_length=100, description="Search query (username)")
    limit: int = Field(default=20, ge=1, le=50, description="Max results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# ============================================================================
# Response Schemas
# ============================================================================

class FriendshipOut(BaseModel):
    """Friendship output"""
    id: int
    requester_id: int
    addressee_id: int
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime
    
    # Populated friend info
    friend: Optional[FriendProfile] = None
    
    class Config:
        orm_mode = True


class FriendRequestOut(BaseModel):
    """Friend request with user info"""
    id: int
    status: FriendshipStatus
    created_at: datetime
    
    # User who sent the request
    requester: FriendProfile
    
    class Config:
        orm_mode = True


class FriendsList(BaseModel):
    """List of friends"""
    friends: list[FriendProfile]
    total: int


class FriendRequestsList(BaseModel):
    """List of friend requests"""
    requests: list[FriendRequestOut]
    total: int


class UserSearchResult(BaseModel):
    """User search results"""
    users: list[FriendProfile]
    total: int
    
    
class FriendshipAction(BaseModel):
    """Generic friendship action response"""
    success: bool
    message: str
    friendship: Optional[FriendshipOut] = None
