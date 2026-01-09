"""
Pet Social API endpoints

Routes:
- GET /api/v1/pets/village - Get pet village (other users' pets)
- POST /api/v1/pets/visit/{user_id} - Visit another user's pet
- POST /api/v1/pets/gift - Send gift to another user
- GET /api/v1/pets/gifts - Get received gifts
- POST /api/v1/pets/gifts/{gift_id}/claim - Claim a gift
- GET /api/v1/pets/leaderboard - Get pet leaderboard
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.pet_social import (
    SendGiftRequest,
    PetVillageUserResponse,
    PetGiftResponse,
    LeaderboardEntry,
)
from app.services.pet_social_service import PetSocialService

router = APIRouter()


@router.get("/village", response_model=List[PetVillageUserResponse])
async def get_pet_village(
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pet village - list of other users' pets
    
    See what other pets are up to!
    """
    try:
        pets = await PetSocialService.get_village(db, str(current_user.id), limit)
        return pets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get village: {str(e)}"
        )


@router.post("/visit/{user_id}")
async def visit_pet(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Visit another user's pet
    
    Record a visit to show social activity
    """
    try:
        result = await PetSocialService.visit_pet(
            db,
            str(current_user.id),
            user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to visit pet: {str(e)}"
        )


@router.post("/gift")
async def send_gift(
    request: SendGiftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a gift to another user's pet
    
    Gifts: treat (happiness+XP), toy (health+XP), hug (both)
    """
    try:
        result = await PetSocialService.send_gift(
            db,
            str(current_user.id),
            request.to_user_id,
            request.gift_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send gift: {str(e)}"
        )


@router.get("/gifts", response_model=List[PetGiftResponse])
async def get_gifts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get received gifts
    
    See what gifts your pet has received!
    """
    try:
        gifts = await PetSocialService.get_gifts(db, str(current_user.id))
        return gifts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gifts: {str(e)}"
        )


@router.post("/gifts/{gift_id}/claim")
async def claim_gift(
    gift_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Claim a received gift
    
    Apply gift effects to your pet!
    """
    try:
        result = await PetSocialService.claim_gift(
            db,
            str(current_user.id),
            gift_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to claim gift: {str(e)}"
        )


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    category: str = Query("level", regex="^(level|games)$"),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pet leaderboard
    
    Categories: level, games
    """
    try:
        leaderboard = await PetSocialService.get_leaderboard(
            db,
            category,
            limit,
        )
        return leaderboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leaderboard: {str(e)}"
        )
