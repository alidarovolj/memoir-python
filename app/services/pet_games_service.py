"""Pet games service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date
from uuid import UUID

from app.models.pet_game import PetGameSession, PetGameStats, GameType
from app.models.pet import Pet


class PetGamesService:
    """Service for pet mini-games"""
    
    DAILY_LIMIT = 3
    
    # XP rewards per game (based on score)
    XP_REWARDS = {
        GameType.FEED_FRENZY: lambda score: min(score, 50),  # Max 50 XP
        GameType.HIDE_AND_SEEK: lambda score: min(score * 10, 30),  # Max 30 XP
        GameType.MEMORY_MATCH: lambda score: min(score * 5, 40),  # Max 40 XP
    }
    
    @staticmethod
    async def can_play_game(db: AsyncSession, user_id: str) -> bool:
        """Check if user can play a game (daily limit)"""
        stats = await PetGamesService._get_or_create_stats(db, user_id)
        
        today = date.today().isoformat()
        
        # Reset daily counter if new day
        if stats.last_played_date != today:
            stats.games_played_today = 0
            stats.last_played_date = today
            await db.commit()
        
        return stats.games_played_today < PetGamesService.DAILY_LIMIT
    
    @staticmethod
    async def play_game(
        db: AsyncSession,
        user_id: str,
        game_type: GameType,
        score: int,
    ) -> dict:
        """Complete a game and get rewards"""
        # Check if can play
        if not await PetGamesService.can_play_game(db, user_id):
            raise ValueError("Daily game limit reached (3 games per day)")
        
        # Get pet
        pet_result = await db.execute(select(Pet).where(Pet.user_id == user_id))
        pet = pet_result.scalar_one_or_none()
        if not pet:
            raise ValueError("Pet not found")
        
        # Calculate XP reward
        xp_calculator = PetGamesService.XP_REWARDS.get(game_type)
        xp_earned = xp_calculator(score) if xp_calculator else 0
        
        # Create game session
        session = PetGameSession(
            user_id=UUID(user_id),
            pet_id=pet.id,
            game_type=game_type,
            score=score,
            xp_earned=xp_earned,
        )
        db.add(session)
        
        # Update pet XP
        pet.xp += xp_earned
        
        # Check for level ups
        level_ups = 0
        evolved = False
        while pet.xp >= pet.xp_for_next_level:
            pet.xp -= pet.xp_for_next_level
            pet.level += 1
            level_ups += 1
            
            if pet.can_evolve():
                evolved = pet.evolve()
        
        # Update stats
        stats = await PetGamesService._get_or_create_stats(db, user_id)
        today = date.today().isoformat()
        
        # Reset daily counter if new day
        if stats.last_played_date != today:
            stats.games_played_today = 0
            stats.last_played_date = today
        
        stats.total_games_played += 1
        stats.total_xp_earned += xp_earned
        stats.games_played_today += 1
        
        # Update per-game stats
        is_high_score = False
        if game_type == GameType.FEED_FRENZY:
            stats.feed_frenzy_plays += 1
            if score > stats.feed_frenzy_high_score:
                stats.feed_frenzy_high_score = score
                is_high_score = True
        elif game_type == GameType.HIDE_AND_SEEK:
            stats.hide_and_seek_plays += 1
            if score > stats.hide_and_seek_high_score:
                stats.hide_and_seek_high_score = score
                is_high_score = True
        elif game_type == GameType.MEMORY_MATCH:
            stats.memory_match_plays += 1
            if score > stats.memory_match_high_score:
                stats.memory_match_high_score = score
                is_high_score = True
        
        await db.commit()
        await db.refresh(session)
        await db.refresh(pet)
        
        return {
            "session": session,
            "pet": pet,
            "xp_earned": xp_earned,
            "level_ups": level_ups,
            "evolved": evolved,
            "is_high_score": is_high_score,
        }
    
    @staticmethod
    async def get_stats(db: AsyncSession, user_id: str) -> dict:
        """Get user's game statistics"""
        stats = await PetGamesService._get_or_create_stats(db, user_id)
        
        today = date.today().isoformat()
        
        # Reset daily counter if new day
        if stats.last_played_date != today:
            stats.games_played_today = 0
            stats.last_played_date = today
            await db.commit()
        
        return {
            "totalGamesPlayed": stats.total_games_played,
            "totalXpEarned": stats.total_xp_earned,
            "gamesPlayedToday": stats.games_played_today,
            "dailyLimit": PetGamesService.DAILY_LIMIT,
            "canPlay": stats.games_played_today < PetGamesService.DAILY_LIMIT,
            "feedFrenzy": {
                "plays": stats.feed_frenzy_plays,
                "highScore": stats.feed_frenzy_high_score,
            },
            "hideAndSeek": {
                "plays": stats.hide_and_seek_plays,
                "highScore": stats.hide_and_seek_high_score,
            },
            "memoryMatch": {
                "plays": stats.memory_match_plays,
                "highScore": stats.memory_match_high_score,
            },
        }
    
    @staticmethod
    async def _get_or_create_stats(db: AsyncSession, user_id: str) -> PetGameStats:
        """Get or create game stats for user"""
        result = await db.execute(
            select(PetGameStats).where(PetGameStats.user_id == user_id)
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = PetGameStats(user_id=UUID(user_id))
            db.add(stats)
            await db.commit()
            await db.refresh(stats)
        
        return stats
