from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from typing import List

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.group_challenge import GroupChallenge, GroupChallengeInvite, group_challenge_members
from app.schemas.group_challenge import CreateGroupChallengeRequest, GroupChallengeOut

router = APIRouter()


@router.post("/group-challenges", response_model=GroupChallengeOut, status_code=status.HTTP_201_CREATED)
async def create_group_challenge(
    request: CreateGroupChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new group challenge"""
    challenge = GroupChallenge(
        creator_id=current_user.id,
        title=request.title,
        description=request.description,
        goal=request.goal,
        goal_type=request.goal_type,
        start_date=request.start_date,
        end_date=request.end_date,
        max_members=request.max_members,
        is_public=request.is_public
    )
    
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    
    # Add creator as first member
    await db.execute(
        insert(group_challenge_members).values(
            challenge_id=challenge.id,
            user_id=current_user.id,
            progress=0,
            completed=False
        )
    )
    await db.commit()
    
    return GroupChallengeOut(
        id=challenge.id,
        creator_id=challenge.creator_id,
        title=challenge.title,
        description=challenge.description,
        goal=challenge.goal,
        goal_type=challenge.goal_type,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        max_members=challenge.max_members,
        is_public=challenge.is_public,
        created_at=challenge.created_at,
        members=[],
        members_count=1
    )


@router.get("/group-challenges", response_model=List[GroupChallengeOut])
async def get_my_group_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's group challenges"""
    # TODO: Implement full logic with member loading
    result = await db.execute(
        select(GroupChallenge).join(
            group_challenge_members,
            group_challenge_members.c.challenge_id == GroupChallenge.id
        ).where(
            group_challenge_members.c.user_id == current_user.id
        ).order_by(GroupChallenge.created_at.desc())
    )
    
    challenges = result.scalars().all()
    
    return [
        GroupChallengeOut(
            id=c.id,
            creator_id=c.creator_id,
            title=c.title,
            description=c.description,
            goal=c.goal,
            goal_type=c.goal_type,
            start_date=c.start_date,
            end_date=c.end_date,
            max_members=c.max_members,
            is_public=c.is_public,
            created_at=c.created_at,
            members=[],
            members_count=0
        )
        for c in challenges
    ]
