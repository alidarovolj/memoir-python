"""Achievement service"""
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.achievement import Achievement, UserAchievement, AchievementType


class AchievementService:
    """Service for managing achievements"""
    
    @staticmethod
    async def get_user_achievements(
        db: AsyncSession,
        user_id: str,
    ) -> dict:
        """Get all achievements with user's progress"""
        # Get all achievements
        achievements_query = select(Achievement).where(Achievement.is_active == True)
        achievements_result = await db.execute(achievements_query)
        all_achievements = achievements_result.scalars().all()
        
        # Get user's progress
        user_achievements_query = select(UserAchievement).where(
            UserAchievement.user_id == UUID(user_id)
        )
        user_achievements_result = await db.execute(user_achievements_query)
        user_achievements = {
            ua.achievement_id: ua for ua in user_achievements_result.scalars().all()
        }
        
        # Categorize
        unlocked = []
        in_progress = []
        locked = []
        
        for achievement in all_achievements:
            user_achievement = user_achievements.get(achievement.id)
            
            if user_achievement:
                progress = user_achievement.progress
                unlocked_status = user_achievement.unlocked
                unlocked_at = user_achievement.unlocked_at
            else:
                progress = 0
                unlocked_status = False
                unlocked_at = None
            
            percentage = min((progress / achievement.criteria_count) * 100, 100) if achievement.criteria_count > 0 else 0
            
            achievement_data = {
                "achievement_id": str(achievement.id),
                "achievement_code": achievement.code,
                "title": achievement.title,
                "description": achievement.description,
                "emoji": achievement.emoji,
                "achievement_type": achievement.achievement_type.value,
                "criteria_count": achievement.criteria_count,
                "progress": progress,
                "unlocked": unlocked_status,
                "unlocked_at": unlocked_at,
                "percentage": round(percentage, 1),
                "xp_reward": achievement.xp_reward,
            }
            
            if unlocked_status:
                unlocked.append(achievement_data)
            elif progress > 0:
                in_progress.append(achievement_data)
            else:
                locked.append(achievement_data)
        
        return {
            "unlocked": unlocked,
            "in_progress": in_progress,
            "locked": locked,
        }
    
    @staticmethod
    async def update_achievement_progress(
        db: AsyncSession,
        user_id: str,
        achievement_code: str,
        increment: int = 1,
    ) -> Optional[UserAchievement]:
        """Update progress on achievement"""
        # Get achievement
        achievement_query = select(Achievement).where(Achievement.code == achievement_code)
        achievement_result = await db.execute(achievement_query)
        achievement = achievement_result.scalar_one_or_none()
        
        if not achievement:
            return None
        
        # Get or create user achievement
        user_achievement_query = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == UUID(user_id),
                UserAchievement.achievement_id == achievement.id,
            )
        )
        user_achievement_result = await db.execute(user_achievement_query)
        user_achievement = user_achievement_result.scalar_one_or_none()
        
        if not user_achievement:
            user_achievement = UserAchievement(
                user_id=UUID(user_id),
                achievement_id=achievement.id,
                progress=0,
                unlocked=False,
            )
            db.add(user_achievement)
        
        if not user_achievement.unlocked:
            user_achievement.progress += increment
            
            # Check if unlocked
            if user_achievement.progress >= achievement.criteria_count:
                user_achievement.unlocked = True
                from datetime import datetime, timezone
                user_achievement.unlocked_at = datetime.now(timezone.utc)
                
                # Award XP to pet
                from app.models.pet import Pet
                pet_query = select(Pet).where(Pet.user_id == UUID(user_id))
                pet_result = await db.execute(pet_query)
                pet = pet_result.scalar_one_or_none()
                
                if pet:
                    pet.xp += achievement.xp_reward
                    pet.check_level_up()
        
        await db.commit()
        await db.refresh(user_achievement)
        
        return user_achievement
