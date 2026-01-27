from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from typing import List

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.friendship import Friendship, FriendshipStatus
from app.models.memory import Memory
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
    memories_count_result = await db.execute(
        select(func.count()).select_from(Memory).where(Memory.user_id == user.id)
    )
    memories_count = memories_count_result.scalar() or 0
    
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
    friends_count = friends_count_result.scalar() or 0
    
    return FriendProfile(
        id=str(user.id),  # Convert UUID to string
        username=user.username or "",
        first_name=user.first_name if hasattr(user, 'first_name') else None,
        last_name=user.last_name if hasattr(user, 'last_name') else None,
        avatar_url=user.avatar_url if hasattr(user, 'avatar_url') else None,
        created_at=user.created_at,
        memories_count=memories_count,
        friends_count=friends_count,
        streak_days=0,  # TODO: Calculate from user activity
        # Personal data
        profession=getattr(user, 'profession', None),
        telegram_url=getattr(user, 'telegram_url', None),
        whatsapp_url=getattr(user, 'whatsapp_url', None),
        youtube_url=getattr(user, 'youtube_url', None),
        linkedin_url=getattr(user, 'linkedin_url', None),
        about_me=getattr(user, 'about_me', None),
        city=getattr(user, 'city', None),
        date_of_birth=getattr(user, 'date_of_birth', None),
        education=getattr(user, 'education', None),
        hobbies=getattr(user, 'hobbies', None),
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
                id=str(req.id),  # Конвертируем int в string
                status=req.status,
                created_at=req.created_at,
                requester=requester_profile
            )
        )
    
    return FriendRequestsList(
        requests=request_list,
        total=len(request_list)
    )


@router.get("/requests/sent", response_model=FriendRequestsList)
async def get_sent_friend_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending friend requests sent by current user
    """
    result = await db.execute(
        select(Friendship).where(
            and_(
                Friendship.requester_id == current_user.id,
                Friendship.status == FriendshipStatus.PENDING
            )
        ).order_by(Friendship.created_at.desc())
    )
    requests = result.scalars().all()
    
    # Load addressee user info
    request_list = []
    for req in requests:
        addressee_result = await db.execute(
            select(User).where(User.id == req.addressee_id)
        )
        addressee = addressee_result.scalar_one()
        addressee_profile = await user_to_friend_profile(addressee, db)
        
        request_list.append(
            FriendRequestOut(
                id=str(req.id),  # Конвертируем int в string
                status=req.status,
                created_at=req.created_at,
                requester=addressee_profile  # В данном случае это получатель запроса
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
        friendship=FriendshipOut(
            id=str(friendship.id),
            requester_id=str(friendship.requester_id),
            addressee_id=str(friendship.addressee_id),
            status=friendship.status,
            created_at=friendship.created_at,
            updated_at=friendship.updated_at,
        )
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
    # Convert request_id from string to integer
    try:
        request_id_int = int(response.request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request_id format"
        )
    
    # Get the friendship request
    result = await db.execute(
        select(Friendship).where(Friendship.id == request_id_int)
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
        friendship=FriendshipOut(
            id=str(friendship.id),
            requester_id=str(friendship.requester_id),
            addressee_id=str(friendship.addressee_id),
            status=friendship.status,
            created_at=friendship.created_at,
            updated_at=friendship.updated_at,
        )
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
    Search for users by username, first name, or last name
    """
    # Search users by username, first_name, or last_name (case-insensitive partial match)
    search_pattern = f"%{search.query}%"
    query = select(User).where(
        and_(
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            ),
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
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            ),
            User.id != current_user.id
        )
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return UserSearchResult(
        users=user_profiles,
        total=total or 0
    )


# ============================================================================
# User Suggestions
# ============================================================================

@router.get("/suggestions", response_model=UserSearchResult)
async def get_user_suggestions(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get suggested users (random users who are not friends yet)
    """
    # Get all users who are not friends with current user
    # First, get list of friend IDs
    friends_query = select(Friendship).where(
        and_(
            or_(
                Friendship.requester_id == current_user.id,
                Friendship.addressee_id == current_user.id
            ),
            Friendship.status == FriendshipStatus.ACCEPTED
        )
    )
    friends_result = await db.execute(friends_query)
    friendships = friends_result.scalars().all()
    
    friend_ids = set()
    for friendship in friendships:
        if friendship.requester_id == current_user.id:
            friend_ids.add(friendship.addressee_id)
        else:
            friend_ids.add(friendship.requester_id)
    
    # Get pending friend request IDs
    pending_query = select(Friendship).where(
        and_(
            or_(
                Friendship.requester_id == current_user.id,
                Friendship.addressee_id == current_user.id
            ),
            Friendship.status == FriendshipStatus.PENDING
        )
    )
    pending_result = await db.execute(pending_query)
    pending_friendships = pending_result.scalars().all()
    
    for friendship in pending_friendships:
        if friendship.requester_id == current_user.id:
            friend_ids.add(friendship.addressee_id)
        else:
            friend_ids.add(friendship.requester_id)
    
    # Get random users excluding friends and current user
    suggestions_query = select(User).where(
        and_(
            User.id != current_user.id,
            User.id.notin_(friend_ids) if friend_ids else True
        )
    ).order_by(func.random()).limit(limit)
    
    result = await db.execute(suggestions_query)
    users = result.scalars().all()
    
    # Convert to FriendProfile
    user_profiles = []
    for user in users:
        profile = await user_to_friend_profile(user, db)
        user_profiles.append(profile)
    
    return UserSearchResult(
        users=user_profiles,
        total=len(user_profiles)
    )


# ============================================================================
# All Users (Potential Friends)
# ============================================================================

@router.get("/users", response_model=UserSearchResult)
async def get_all_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users (potential friends) excluding current user and their friends
    
    Returns paginated list of users who are not friends with current user
    """
    # Get list of friend IDs (accepted and pending)
    friends_query = select(Friendship).where(
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        )
    )
    friends_result = await db.execute(friends_query)
    friendships = friends_result.scalars().all()
    
    friend_ids = {current_user.id}  # Include current user to exclude them
    for friendship in friendships:
        if friendship.requester_id == current_user.id:
            friend_ids.add(friendship.addressee_id)
        else:
            friend_ids.add(friendship.requester_id)
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get all users excluding friends and current user
    users_query = select(User).where(
        User.id.notin_(friend_ids) if friend_ids else True
    ).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(users_query)
    users = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(User).where(
        User.id.notin_(friend_ids) if friend_ids else True
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Convert to FriendProfile
    user_profiles = []
    for user in users:
        profile = await user_to_friend_profile(user, db)
        user_profiles.append(profile)
    
    return UserSearchResult(
        users=user_profiles,
        total=total
    )
