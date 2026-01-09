"""
Pet Games API endpoints

Routes:
- POST /api/v1/pets/games/play - Complete a game
- GET /api/v1/pets/games/stats - Get game statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.pet_games import (
    CompleteGameRequest,
    GameSessionResponse,
    GameStatsResponse,
)
from app.services.pet_games_service import PetGamesService

router = APIRouter()


@router.post("/games/play")
async def play_game(
    request: CompleteGameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Complete a mini-game and get rewards
    
    Daily limit: 3 games per day
    Rewards XP based on score
    """
    try:
        result = await PetGamesService.play_game(
            db,
            str(current_user.id),
            request.game_type,
            request.score,
        )
        
        message = f"🎮 Earned {result['xp_earned']} XP!"
        if result['is_high_score']:
            message += " 🏆 New high score!"
        if result['level_ups'] > 0:
            message += f" 🎉 Level up! Now level {result['pet'].level}!"
        if result['evolved']:
            message += f" ✨ Pet evolved to {result['pet'].evolution_stage.value}!"
        
        return {
            "message": message,
            "session": {
                "id": str(result['session'].id),
                "gameType": result['session'].game_type.value,
                "score": result['session'].score,
                "xpEarned": result['session'].xp_earned,
                "playedAt": str(result['session'].played_at),
                "isHighScore": result['is_high_score'],
            },
            "pet": {
                "level": result['pet'].level,
                "xp": result['pet'].xp,
                "xpForNextLevel": result['pet'].xp_for_next_level,
            },
            "levelUps": result['level_ups'],
            "evolved": result['evolved'],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to play game: {str(e)}"
        )


@router.get("/games/stats", response_model=GameStatsResponse)
async def get_game_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's game statistics
    
    Shows total games played, XP earned, and per-game stats
    """
    try:
        stats = await PetGamesService.get_stats(db, str(current_user.id))
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
