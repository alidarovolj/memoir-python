from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from typing import List
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.memory import Memory
from app.models.memory_reactions import MemoryReaction, MemoryComment, ReactionType
from app.schemas.memory_reactions import (
    AddReactionRequest,
    RemoveReactionRequest,
    AddCommentRequest,
    UpdateCommentRequest,
    DeleteCommentRequest,
    ReactionOut,
    ReactionsSummary,
    CommentOut,
    CommentWithReplies,
    CommentsList,
    ReactionActionResponse,
    CommentActionResponse,
    UserInfo
)

router = APIRouter()


# ============================================================================
# Reactions
# ============================================================================

@router.post("/reactions", response_model=ReactionActionResponse)
async def add_reaction(
    request: AddReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add or update reaction to memory"""
    # Check if user already reacted
    result = await db.execute(
        select(MemoryReaction).where(
            and_(
                MemoryReaction.memory_id == request.memory_id,
                MemoryReaction.user_id == current_user.id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update reaction type
        existing.reaction_type = request.reaction_type
    else:
        # Create new reaction
        reaction = MemoryReaction(
            memory_id=request.memory_id,
            user_id=current_user.id,
            reaction_type=request.reaction_type
        )
        db.add(reaction)
    
    await db.commit()
    
    # Get summary
    summary = await get_reactions_summary(db, request.memory_id, current_user.id)
    
    return ReactionActionResponse(
        success=True,
        message="Reaction added",
        memory_id=request.memory_id,
        reactions_summary=summary
    )


@router.delete("/reactions", response_model=ReactionActionResponse)
async def remove_reaction(
    request: RemoveReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove reaction from memory"""
    await db.execute(
        delete(MemoryReaction).where(
            and_(
                MemoryReaction.memory_id == request.memory_id,
                MemoryReaction.user_id == current_user.id
            )
        )
    )
    await db.commit()
    
    summary = await get_reactions_summary(db, request.memory_id, current_user.id)
    
    return ReactionActionResponse(
        success=True,
        message="Reaction removed",
        memory_id=request.memory_id,
        reactions_summary=summary
    )


@router.get("/{memory_id}/reactions", response_model=ReactionsSummary)
async def get_memory_reactions(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reactions summary for memory"""
    return await get_reactions_summary(db, memory_id, current_user.id)


async def get_reactions_summary(
    db: AsyncSession,
    memory_id: UUID,
    user_id: UUID
) -> ReactionsSummary:
    """Helper to get reactions summary"""
    # Count by type
    result = await db.execute(
        select(
            MemoryReaction.reaction_type,
            func.count(MemoryReaction.id)
        ).where(
            MemoryReaction.memory_id == memory_id
        ).group_by(MemoryReaction.reaction_type)
    )
    
    counts = dict(result.all())
    
    # Get user's reaction
    user_reaction_result = await db.execute(
        select(MemoryReaction.reaction_type).where(
            and_(
                MemoryReaction.memory_id == memory_id,
                MemoryReaction.user_id == user_id
            )
        )
    )
    user_reaction = user_reaction_result.scalar_one_or_none()
    
    return ReactionsSummary(
        like=counts.get(ReactionType.LIKE, 0),
        love=counts.get(ReactionType.LOVE, 0),
        fire=counts.get(ReactionType.FIRE, 0),
        star=counts.get(ReactionType.STAR, 0),
        celebrate=counts.get(ReactionType.CELEBRATE, 0),
        thinking=counts.get(ReactionType.THINKING, 0),
        total=sum(counts.values()),
        user_reaction=user_reaction
    )


# ============================================================================
# Comments
# ============================================================================

@router.post("/comments", response_model=CommentActionResponse)
async def add_comment(
    request: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add comment to memory"""
    comment = MemoryComment(
        memory_id=request.memory_id,
        user_id=current_user.id,
        text=request.text,
        parent_id=request.parent_id
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Get user info
    user_info = UserInfo(user_id=current_user.id, username=current_user.username)
    
    comment_out = CommentOut(
        id=comment.id,
        memory_id=comment.memory_id,
        user=user_info,
        text=comment.text,
        parent_id=comment.parent_id,
        replies_count=0,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_edited=False
    )
    
    return CommentActionResponse(
        success=True,
        message="Comment added",
        comment=comment_out
    )


@router.get("/{memory_id}/comments", response_model=CommentsList)
async def get_memory_comments(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all comments for memory"""
    # Get top-level comments (no parent)
    result = await db.execute(
        select(MemoryComment, User).join(User).where(
            and_(
                MemoryComment.memory_id == memory_id,
                MemoryComment.parent_id.is_(None)
            )
        ).order_by(MemoryComment.created_at.desc())
    )
    
    top_comments = result.all()
    
    comments_with_replies = []
    for comment, user in top_comments:
        # Get replies count
        replies_result = await db.execute(
            select(func.count()).select_from(MemoryComment).where(
                MemoryComment.parent_id == comment.id
            )
        )
        replies_count = replies_result.scalar()
        
        user_info = UserInfo(user_id=user.id, username=user.username)
        
        comment_out = CommentWithReplies(
            id=comment.id,
            memory_id=comment.memory_id,
            user=user_info,
            text=comment.text,
            parent_id=comment.parent_id,
            replies_count=replies_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            is_edited=comment.created_at != comment.updated_at,
            replies=[]
        )
        
        comments_with_replies.append(comment_out)
    
    return CommentsList(
        comments=comments_with_replies,
        total=len(comments_with_replies)
    )


@router.delete("/comments/{comment_id}", response_model=CommentActionResponse)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete comment"""
    result = await db.execute(
        select(MemoryComment).where(MemoryComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        # Return success if comment doesn't exist (idempotent delete)
        return CommentActionResponse(
            success=True,
            message="Comment not found or already deleted",
            comment=None
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    await db.delete(comment)
    await db.commit()
    
    return CommentActionResponse(
        success=True,
        message="Comment deleted",
        comment=None
    )
