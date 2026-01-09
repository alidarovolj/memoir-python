"""Challenge API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import math

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.challenge import (
    GlobalChallenge,
    GlobalChallengeCreate,
    GlobalChallengeUpdate,
    ChallengeList,
    ChallengeParticipant,
    ChallengeProgress,
    ChallengeLeaderboard,
    LeaderboardEntry,
)
from app.services.challenge_service import ChallengeService

router = APIRouter()


@router.get("/active", response_model=ChallengeList)
async def get_active_challenges(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active challenges (ongoing or upcoming)"""
    challenges, total = await ChallengeService.get_active_challenges(db, page, size)
    
    # Add computed fields
    now = datetime.now(timezone.utc)
    items_with_computed = []
    
    for challenge in challenges:
        challenge_dict = {
            **challenge.__dict__,
            "is_ongoing": challenge.start_date <= now <= challenge.end_date,
            "days_remaining": max(0, (challenge.end_date - now).days),
        }
        items_with_computed.append(challenge_dict)
    
    pages = math.ceil(total / size) if total > 0 else 0
    
    return {
        "items": items_with_computed,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.get("/{challenge_id}", response_model=GlobalChallenge)
async def get_challenge(
    challenge_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get challenge details"""
    challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
    
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    
    now = datetime.now(timezone.utc)
    challenge_dict = {
        **challenge.__dict__,
        "is_ongoing": challenge.start_date <= now <= challenge.end_date,
        "days_remaining": max(0, (challenge.end_date - now).days),
    }
    
    return challenge_dict


@router.post("/{challenge_id}/join", response_model=ChallengeParticipant)
async def join_challenge(
    challenge_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a challenge"""
    # Check if challenge exists
    challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    
    # Check if challenge is still joinable
    now = datetime.now(timezone.utc)
    if now > challenge.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge has already ended",
        )
    
    participant = await ChallengeService.join_challenge(
        db,
        challenge_id=challenge_id,
        user_id=str(current_user.id),
    )
    
    return participant


@router.get("/{challenge_id}/progress", response_model=ChallengeProgress)
async def get_my_progress(
    challenge_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's progress in a challenge"""
    challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    
    participant = await ChallengeService.get_user_progress(
        db,
        challenge_id=challenge_id,
        user_id=str(current_user.id),
    )
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not participating in this challenge",
        )
    
    # Get leaderboard to find rank
    leaderboard = await ChallengeService.get_leaderboard(db, challenge_id)
    user_rank = None
    for entry in leaderboard:
        if entry["user_id"] == str(current_user.id):
            user_rank = entry["rank"]
            break
    
    target = challenge.goal.get("target", 1)
    percentage = min((participant.progress / target) * 100, 100) if target > 0 else 0
    
    return {
        "challenge_id": challenge.id,
        "challenge_title": challenge.title,
        "challenge_emoji": challenge.emoji,
        "goal": challenge.goal,
        "progress": participant.progress,
        "target": target,
        "completed": participant.completed,
        "percentage": round(percentage, 1),
        "rank": user_rank,
        "joined_at": participant.joined_at,
    }


@router.get("/{challenge_id}/leaderboard", response_model=ChallengeLeaderboard)
async def get_challenge_leaderboard(
    challenge_id: str,
    limit: int = Query(100, ge=1, le=500, description="Max entries to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get challenge leaderboard"""
    challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    
    leaderboard = await ChallengeService.get_leaderboard(db, challenge_id, limit)
    
    # Find current user's rank
    user_rank = None
    for entry in leaderboard:
        if entry["user_id"] == str(current_user.id):
            user_rank = entry["rank"]
            break
    
    return {
        "challenge_id": challenge.id,
        "challenge_title": challenge.title,
        "entries": leaderboard,
        "total_participants": challenge.participants_count,
        "user_rank": user_rank,
    }


@router.get("/my/participations", response_model=list[ChallengeProgress])
async def get_my_challenges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all challenges current user is participating in"""
    user_challenges = await ChallengeService.get_user_challenges(
        db,
        user_id=str(current_user.id),
    )
    
    return user_challenges


# Admin endpoints (TODO: add proper admin authentication)
@router.post("", response_model=GlobalChallenge, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    challenge_data: GlobalChallengeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new challenge (admin only)"""
    challenge = await ChallengeService.create_challenge(db, challenge_data)
    
    now = datetime.now(timezone.utc)
    challenge_dict = {
        **challenge.__dict__,
        "is_ongoing": challenge.start_date <= now <= challenge.end_date,
        "days_remaining": max(0, (challenge.end_date - now).days),
    }
    
    return challenge_dict
