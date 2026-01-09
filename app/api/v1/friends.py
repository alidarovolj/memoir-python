from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from typing import List

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.friendship import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendRemove,
    UserSearch,
    FriendProfile,
    FriendsList,
    FriendRequestsList,
    FriendRequestOut,
    UserSearchResult,
    FriendshipAction,
    FriendshipOut
)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

async def get_friendship_between_users(
    db: AsyncSession,
    user1_id: int,
    user2_id: int
) -> Friendship | None:
    """Get friendship between two users (regardless of who initiated)"""
    result = await db.execute(
        select(Friendship).where(
            or_(
                and_(
                    Friendship.requester_id == user1_id,
                    Friendship.addressee_id == user2_id
                ),
                and_(
                    Friendship.requester_id == user2_id,
                    Friendship.addressee_id == user1_id
                )
            )
        )
    )
    return result.scalar_one_or_none()


async def user_to_friend_profile(user: User, db: AsyncSession) -> FriendProfile:
    """Convert User model to FriendProfile with stats"""
    # Count memories
    memories_count = await db.scalar(
        select(func.count()).select_from(User).where(User.id == user.id)
    )
    
    # Count friends
    friends_count_result = await db.execute(
        select(func.count()).select_from(Friendship).where(
            and_(
                or_(
                    Friendship.requester_id == user.id,
                    Friendship.addressee_id == user.id
                ),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    friends_count = friends_count_result.scalar()
    
    return FriendProfile(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url if hasattr(user, 'avatar_url') else None,
        created_at=user.created_at,
        memories_count=memories_count or 0,
        friends_count=friends_count or 0,
        streak_days=0  # TODO: Calculate from user activity
    )


# ============================================================================
# Friends List
# ============================================================================

@router.get("/", response_model=FriendsList)
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of user's friends (accepted friendships only)
    """
    # Get all friendships where user is involved and status is accepted
    result = await db.execute(
        select(Friendship).where(
            and_(
                or_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == current_user.id
                ),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    friendships = result.scalars().all()
    
    # Get friend user objects
    friend_ids = []
    for friendship in friendships:
        if friendship.requester_id == current_user.id:
            friend_ids.append(friendship.addressee_id)
        else:
            friend_ids.append(friendship.requester_id)
    
    if not friend_ids:
        return FriendsList(friends=[], total=0)
    
    # Fetch friend users
    friends_result = await db.execute(
        select(User).where(User.id.in_(friend_ids))
    )
    friends = friends_result.scalars().all()
    
    # Convert to FriendProfile
    friend_profiles = []
    for friend in friends:
        profile = await user_to_friend_profile(friend, db)
        friend_profiles.append(profile)
    
    return FriendsList(
        friends=friend_profiles,
        total=len(friend_profiles)
    )


# ============================================================================
# Friend Requests
# ============================================================================

@router.get("/requests", response_model=FriendRequestsList)
async def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending friend requests (received by current user)
    """
    result = await db.execute(
        select(Friendship).where(
            and_(
                Friendship.addressee_id == current_user.id,
                Friendship.status == FriendshipStatus.PENDING
            )
        ).order_by(Friendship.created_at.desc())
    )
    requests = result.scalars().all()
    
    # Load requester user info
    request_list = []
    for req in requests:
        requester_result = await db.execute(
            select(User).where(User.id == req.requester_id)
        )
        requester = requester_result.scalar_one()
        requester_profile = await user_to_friend_profile(requester, db)
        
        request_list.append(
            FriendRequestOut(
                id=req.id,
                status=req.status,
                created_at=req.created_at,
                requester=requester_profile
            )
        )
    
    return FriendRequestsList(
        requests=request_list,
        total=len(request_list)
    )


@router.post("/requests", response_model=FriendshipAction, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a friend request to another user
    """
    # Validate: can't befriend yourself
    if request.addressee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself"
        )
    
    # Check if addressee exists
    addressee_result = await db.execute(
        select(User).where(User.id == request.addressee_id)
    )
    addressee = addressee_result.scalar_one_or_none()
    
    if not addressee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if friendship already exists
    existing = await get_friendship_between_users(db, current_user.id, request.addressee_id)
    
    if existing:
        if existing.status == FriendshipStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already friends"
            )
        elif existing.status == FriendshipStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Friend request already sent"
            )
        elif existing.status == FriendshipStatus.BLOCKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot send friend request to this user"
            )
    
    # Create new friendship request
    friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=request.addressee_id,
        status=FriendshipStatus.PENDING
    )
    
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)
    
    return FriendshipAction(
        success=True,
        message="Friend request sent successfully",
        friendship=FriendshipOut.from_orm(friendship)
    )


@router.post("/requests/respond", response_model=FriendshipAction)
async def respond_to_friend_request(
    response: FriendRequestResponse,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accept or reject a friend request
    """
    # Get the friendship request
    result = await db.execute(
        select(Friendship).where(Friendship.id == response.request_id)
    )
    friendship = result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    # Validate: must be addressee to respond
    if friendship.addressee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond to requests sent to you"
        )
    
    # Validate: must be pending
    if friendship.status != FriendshipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request is no longer pending"
        )
    
    # Update status
    if response.action == "accept":
        friendship.status = FriendshipStatus.ACCEPTED
        message = "Friend request accepted"
    else:  # reject
        friendship.status = FriendshipStatus.REJECTED
        message = "Friend request rejected"
    
    await db.commit()
    await db.refresh(friendship)
    
    return FriendshipAction(
        success=True,
        message=message,
        friendship=FriendshipOut.from_orm(friendship)
    )


# ============================================================================
# Remove Friend
# ============================================================================

@router.delete("/remove", response_model=FriendshipAction)
async def remove_friend(
    remove_request: FriendRemove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a friend (delete friendship)
    """
    # Get friendship
    friendship = await get_friendship_between_users(db, current_user.id, remove_request.friend_id)
    
    if not friendship:
        # Return success if friendship doesn't exist (idempotent delete)
        return FriendshipAction(
            success=True,
            message="Friendship not found or already removed",
            friendship=None
        )
    
    if friendship.status != FriendshipStatus.ACCEPTED:
        # Return success if not currently friends (already in desired state)
        return FriendshipAction(
            success=True,
            message="Not currently friends",
            friendship=None
        )
    
    # Delete friendship
    await db.delete(friendship)
    await db.commit()
    
    return FriendshipAction(
        success=True,
        message="Friend removed successfully",
        friendship=None
    )


# ============================================================================
# User Search
# ============================================================================

@router.post("/search", response_model=UserSearchResult)
async def search_users(
    search: UserSearch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for users by username
    """
    # Search users by username (case-insensitive partial match)
    query = select(User).where(
        and_(
            User.username.ilike(f"%{search.query}%"),
            User.id != current_user.id  # Exclude self
        )
    ).limit(search.limit).offset(search.offset)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Convert to FriendProfile
    user_profiles = []
    for user in users:
        profile = await user_to_friend_profile(user, db)
        user_profiles.append(profile)
    
    # Get total count
    count_query = select(func.count()).select_from(User).where(
        and_(
            User.username.ilike(f"%{search.query}%"),
            User.id != current_user.id
        )
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return UserSearchResult(
        users=user_profiles,
        total=total or 0
    )
