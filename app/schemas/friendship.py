from pydantic import BaseModel, Field, validator, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    
    id: str  # Changed from int to str for UUID support
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    
    # Stats (optional, можно добавить позже)
    memories_count: Optional[int] = 0
    friends_count: Optional[int] = 0
    streak_days: Optional[int] = 0
    
    # Personal data
    profession: Optional[str] = None
    telegram_url: Optional[str] = None
    whatsapp_url: Optional[str] = None
    youtube_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    education: Optional[str] = None
    hobbies: Optional[str] = None


# ============================================================================
# Request Schemas
# ============================================================================

class FriendRequestCreate(BaseModel):
    """Send friend request"""
    addressee_id: str = Field(..., description="ID of user to befriend")


class FriendRequestResponse(BaseModel):
    """Respond to friend request"""
    request_id: str = Field(..., description="ID of friendship request")
    action: str = Field(..., description="Action: 'accept' or 'reject'")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['accept', 'reject']:
            raise ValueError('action must be "accept" or "reject"')
        return v


class FriendRemove(BaseModel):
    """Remove friend"""
    friend_id: str = Field(..., description="ID of friend to remove")


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
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    requester_id: str
    addressee_id: str
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime
    
    # Populated friend info
    friend: Optional[FriendProfile] = None


class FriendRequestOut(BaseModel):
    """Friend request with user info"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: FriendshipStatus
    created_at: datetime
    
    # User who sent the request
    requester: FriendProfile


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
