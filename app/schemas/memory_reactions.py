from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.memory_reactions import ReactionType


# ============================================================================
# Request Schemas
# ============================================================================

class AddReactionRequest(BaseModel):
    """Add reaction to memory"""
    memory_id: UUID
    reaction_type: ReactionType = Field(default=ReactionType.LIKE)


class RemoveReactionRequest(BaseModel):
    """Remove reaction from memory"""
    memory_id: UUID


class AddCommentRequest(BaseModel):
    """Add comment to memory"""
    memory_id: UUID
    text: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[int] = Field(default=None, description="Parent comment ID for replies")


class UpdateCommentRequest(BaseModel):
    """Update comment"""
    comment_id: int
    text: str = Field(..., min_length=1, max_length=1000)


class DeleteCommentRequest(BaseModel):
    """Delete comment"""
    comment_id: int


# ============================================================================
# Response Schemas
# ============================================================================

class UserInfo(BaseModel):
    """Basic user info for reactions/comments"""
    user_id: UUID
    username: str
    
    class Config:
        orm_mode = True


class ReactionOut(BaseModel):
    """Reaction output"""
    id: int
    memory_id: UUID
    user: UserInfo
    reaction_type: ReactionType
    created_at: datetime
    
    class Config:
        orm_mode = True


class ReactionsSummary(BaseModel):
    """Summary of reactions by type"""
    like: int = 0
    love: int = 0
    fire: int = 0
    star: int = 0
    celebrate: int = 0
    thinking: int = 0
    total: int = 0
    user_reaction: Optional[ReactionType] = None  # Current user's reaction


class CommentOut(BaseModel):
    """Comment output"""
    id: int
    memory_id: UUID
    user: UserInfo
    text: str
    parent_id: Optional[int] = None
    replies_count: int = 0
    created_at: datetime
    updated_at: datetime
    is_edited: bool = False
    
    class Config:
        orm_mode = True


class CommentWithReplies(CommentOut):
    """Comment with its replies"""
    replies: List[CommentOut] = []


class CommentsList(BaseModel):
    """List of comments"""
    comments: List[CommentWithReplies]
    total: int


class ReactionActionResponse(BaseModel):
    """Response for reaction actions"""
    success: bool
    message: str
    memory_id: UUID
    reactions_summary: ReactionsSummary


class CommentActionResponse(BaseModel):
    """Response for comment actions"""
    success: bool
    message: str
    comment: Optional[CommentOut] = None
