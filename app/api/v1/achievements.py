"""Achievement API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.achievement import AchievementList
from app.services.achievement_service import AchievementService

router = APIRouter()


@router.get("", response_model=AchievementList)
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all achievements with user's progress
    
    Returns:
    - unlocked: Achievements user has completed
    - in_progress: Achievements with progress > 0
    - locked: Achievements not started yet
    """
    result = await AchievementService.get_user_achievements(
        db=db,
        user_id=str(current_user.id),
    )
    
    return result
