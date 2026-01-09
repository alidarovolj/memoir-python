from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, insert, delete, func
from typing import List
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.memory import Memory, PrivacyLevel
from app.models.memory_share import memory_shares, MemoryShareHistory
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.memory_share import (
    ShareMemoryRequest,
    UpdateMemoryPrivacy,
    UnshareMemoryRequest,
    MemoryShareInfo,
    SharedWithUser,
    SharedMemoriesList,
    SharedMemoryListItem,
    ShareActionResponse
)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

async def verify_memory_owner(
    db: AsyncSession,
    memory_id: UUID,
    user_id: UUID
) -> Memory:
    """Verify that user owns the memory"""
    result = await db.execute(
        select(Memory).where(
            and_(
                Memory.id == memory_id,
                Memory.user_id == user_id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found or you don't have permission"
        )
    
    return memory


async def verify_friendship(
    db: AsyncSession,
    user1_id: UUID,
    user2_id: UUID
) -> bool:
    """Check if two users are friends"""
    result = await db.execute(
        select(Friendship).where(
            and_(
                or_(
                    and_(
                        Friendship.requester_id == user1_id,
                        Friendship.addressee_id == user2_id
                    ),
                    and_(
                        Friendship.requester_id == user2_id,
                        Friendship.addressee_id == user1_id
                    )
                ),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    return result.scalar_one_or_none() is not None


# ============================================================================
# Share Memory
# ============================================================================

@router.post("/share", response_model=ShareActionResponse)
async def share_memory(
    request: ShareMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Share a memory with specific users
    """
    # Verify ownership
    memory = await verify_memory_owner(db, request.memory_id, current_user.id)
    
    # Validate that all recipients are friends
    for user_id in request.user_ids:
        if user_id == current_user.id:  # Can't share with self
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot share memory with yourself"
            )
        
        # Check friendship
        is_friend = await verify_friendship(db, current_user.id, user_id)
        if not is_friend:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} is not your friend"
            )
    
    # Update memory privacy to SHARED if not already
    if memory.privacy_level == PrivacyLevel.PRIVATE:
        memory.privacy_level = PrivacyLevel.SHARED
    
    # Add shares
    shares_added = 0
    for user_id in request.user_ids:
        # Check if already shared
        existing = await db.execute(
            select(memory_shares).where(
                and_(
                    memory_shares.c.memory_id == request.memory_id,
                    memory_shares.c.shared_with_user_id == user_id
                )
            )
        )
        
        if not existing.first():
            # Insert share
            await db.execute(
                insert(memory_shares).values(
                    memory_id=request.memory_id,
                    shared_with_user_id=user_id,
                    can_comment=request.can_comment,
                    can_react=request.can_react
                )
            )
            
            # Add to history
            history = MemoryShareHistory(
                memory_id=request.memory_id,
                shared_by_user_id=current_user.id,
                shared_with_user_id=user_id
            )
            db.add(history)
            shares_added += 1
    
    await db.commit()
    
    return ShareActionResponse(
        success=True,
        message=f"Memory shared with {shares_added} user(s)",
        memory_id=request.memory_id,
        shared_with_count=shares_added
    )


# ============================================================================
# Unshare Memory
# ============================================================================

@router.post("/unshare", response_model=ShareActionResponse)
async def unshare_memory(
    request: UnshareMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove sharing for specific users
    """
    # Verify ownership
    await verify_memory_owner(db, request.memory_id, current_user.id)
    
    # Delete shares
    result = await db.execute(
        delete(memory_shares).where(
            and_(
                memory_shares.c.memory_id == request.memory_id,
                memory_shares.c.shared_with_user_id.in_(request.user_ids)
            )
        )
    )
    
    await db.commit()
    
    return ShareActionResponse(
        success=True,
        message=f"Memory unshared from {result.rowcount} user(s)",
        memory_id=request.memory_id,
        shared_with_count=result.rowcount
    )


# ============================================================================
# Update Privacy
# ============================================================================

@router.put("/privacy", response_model=ShareActionResponse)
async def update_memory_privacy(
    request: UpdateMemoryPrivacy,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update memory privacy level
    """
    memory = await verify_memory_owner(db, request.memory_id, current_user.id)
    
    memory.privacy_level = request.privacy_level
    await db.commit()
    
    return ShareActionResponse(
        success=True,
        message=f"Privacy updated to {request.privacy_level.value}",
        memory_id=request.memory_id,
        shared_with_count=0
    )


# ============================================================================
# Get Share Info
# ============================================================================

@router.get("/{memory_id}/info", response_model=MemoryShareInfo)
async def get_memory_share_info(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about who memory is shared with
    """
    memory = await verify_memory_owner(db, memory_id, current_user.id)
    
    # Get all shares
    result = await db.execute(
        select(
            memory_shares.c.shared_with_user_id,
            memory_shares.c.can_comment,
            memory_shares.c.can_react,
            memory_shares.c.created_at,
            User.username,
            MemoryShareHistory.viewed_at
        ).select_from(memory_shares)
        .join(User, User.id == memory_shares.c.shared_with_user_id)
        .outerjoin(
            MemoryShareHistory,
            and_(
                MemoryShareHistory.memory_id == memory_id,
                MemoryShareHistory.shared_with_user_id == memory_shares.c.shared_with_user_id
            )
        )
        .where(memory_shares.c.memory_id == memory_id)
    )
    
    shares = result.all()
    
    shared_with_users = [
        SharedWithUser(
            user_id=share.shared_with_user_id,
            username=share.username,
            can_comment=share.can_comment,
            can_react=share.can_react,
            shared_at=share.created_at,
            viewed_at=share.viewed_at
        )
        for share in shares
    ]
    
    return MemoryShareInfo(
        memory_id=memory_id,
        privacy_level=memory.privacy_level,
        shared_with=shared_with_users,
        total_shares=len(shared_with_users)
    )


# ============================================================================
# Get Shared Memories (received)
# ============================================================================

@router.get("/received", response_model=SharedMemoriesList)
async def get_shared_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get memories shared with current user
    """
    # Query memories shared with user
    result = await db.execute(
        select(
            Memory,
            memory_shares.c.created_at.label("shared_at"),
            memory_shares.c.can_comment,
            memory_shares.c.can_react,
            User.username.label("owner_username"),
            MemoryShareHistory.viewed_at
        ).select_from(memory_shares)
        .join(Memory, Memory.id == memory_shares.c.memory_id)
        .join(User, User.id == Memory.user_id)
        .outerjoin(
            MemoryShareHistory,
            and_(
                MemoryShareHistory.memory_id == Memory.id,
                MemoryShareHistory.shared_with_user_id == current_user.id
            )
        )
        .where(memory_shares.c.shared_with_user_id == current_user.id)
        .order_by(memory_shares.c.created_at.desc())
    )
    
    rows = result.all()
    
    memories = [
        SharedMemoryListItem(
            memory_id=row.Memory.id,
            title=row.Memory.title,
            content=row.Memory.content,
            image_url=row.Memory.image_url,
            created_at=row.Memory.created_at,
            owner_id=row.Memory.user_id,
            owner_username=row.owner_username,
            shared_at=row.shared_at,
            can_comment=row.can_comment,
            can_react=row.can_react,
            viewed_at=row.viewed_at
        )
        for row in rows
    ]
    
    return SharedMemoriesList(
        memories=memories,
        total=len(memories)
    )
