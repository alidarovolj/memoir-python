"""Memory service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.models.memory import Memory
from app.models.category import Category
from app.models.memory_reactions import MemoryReaction, MemoryComment
from app.models.memory_share import memory_shares
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.core.exceptions import NotFoundError, AuthorizationError


class MemoryService:
    """Memory service"""
    
    @staticmethod
    async def create_memory(
        db: AsyncSession, 
        user_id: str, 
        memory_data: MemoryCreate
    ) -> Memory:
        """Create a new memory"""
        # Verify category exists if provided
        if memory_data.category_id:
            result = await db.execute(
                select(Category).where(Category.id == memory_data.category_id)
            )
            if not result.scalar_one_or_none():
                raise NotFoundError("Category not found")
        
        new_memory = Memory(
            user_id=user_id,
            title=memory_data.title,
            content=memory_data.content,
            source_type=memory_data.source_type,
            source_url=memory_data.source_url,
            image_url=memory_data.image_url,
            backdrop_url=memory_data.backdrop_url,
            audio_url=memory_data.audio_url,
            audio_transcript=memory_data.audio_transcript,
            memory_metadata=memory_data.memory_metadata or {},
            category_id=memory_data.category_id,
            related_task_id=memory_data.related_task_id,
        )
        
        print(f"✅ [SERVICE] Memory object created:")
        print(f"   - image_url: {new_memory.image_url}")
        print(f"   - backdrop_url: {new_memory.backdrop_url}")
        print(f"   - audio_url: {new_memory.audio_url}")
        print(f"   - audio_transcript: {new_memory.audio_transcript}")
        
        db.add(new_memory)
        await db.commit()
        await db.refresh(new_memory)
        
        print(f"✅ [SERVICE] Memory saved to DB with ID: {new_memory.id}")
        print(f"   - image_url: {new_memory.image_url}")
        print(f"   - backdrop_url: {new_memory.backdrop_url}")
        print(f"   - audio_url: {new_memory.audio_url}")
        print(f"   - audio_transcript: {new_memory.audio_transcript}")
        
        # Update achievements
        try:
            from app.services.achievement_service import AchievementService
            from app.models.achievement import AchievementType, Achievement, UserAchievement
            
            # Count total memories for user (after this new one)
            count_result = await db.execute(
                select(func.count()).select_from(Memory).where(Memory.user_id == user_id)
            )
            total_memories = count_result.scalar() or 0
            
            print(f"🏆 [SERVICE] Updating achievements for user {user_id}, total memories: {total_memories}")
            
            # Get all memory-related achievements
            achievements_query = select(Achievement).where(
                Achievement.achievement_type == AchievementType.MEMORIES,
                Achievement.is_active == True
            )
            achievements_result = await db.execute(achievements_query)
            memory_achievements = achievements_result.scalars().all()
            
            for achievement in memory_achievements:
                try:
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
                    
                    # Sync progress to current memory count (but don't decrease)
                    if not user_achievement.unlocked:
                        # Set progress to current total if it's less
                        if user_achievement.progress < total_memories:
                            user_achievement.progress = total_memories
                            
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
                                
                                print(f"🏆 [SERVICE] Achievement unlocked: {achievement.code}!")
                        
                        await db.commit()
                        await db.refresh(user_achievement)
                        print(f"🏆 [SERVICE] Synced achievement: {achievement.code} (progress: {user_achievement.progress}/{achievement.criteria_count})")
                except Exception as e:
                    print(f"⚠️ [SERVICE] Error updating achievement {achievement.code}: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"⚠️ [SERVICE] Error updating achievements: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail memory creation if achievements fail
        
        return new_memory
    
    @staticmethod
    async def get_memories(
        db: AsyncSession,
        user_id: str,
        category_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Memory], int]:
        """Get paginated list of memories"""
        # Build base query
        query = select(Memory).where(Memory.user_id == user_id)
        
        # Filter by category if provided
        if category_id:
            query = query.where(Memory.category_id == category_id)
        
        # Get total count
        count_query = select(func.count()).select_from(Memory).where(Memory.user_id == user_id)
        if category_id:
            count_query = count_query.where(Memory.category_id == category_id)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.options(selectinload(Memory.category))
        query = query.order_by(Memory.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return list(memories), total
    
    @staticmethod
    async def get_memory_by_id(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> Memory:
        """Get memory by ID"""
        query = select(Memory).where(
            and_(Memory.id == memory_id, Memory.user_id == user_id)
        ).options(selectinload(Memory.category))
        
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise NotFoundError("Memory not found")
        
        return memory
    
    @staticmethod
    async def has_memory_for_task(
        db: AsyncSession,
        task_id: str,
        user_id: str,
    ) -> bool:
        """Check if there is a memory linked to this task"""
        query = select(func.count()).select_from(Memory).where(
            and_(
                Memory.related_task_id == task_id,
                Memory.user_id == user_id,
            )
        )
        
        result = await db.execute(query)
        count = result.scalar() or 0
        
        return count > 0
    
    @staticmethod
    async def update_memory(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
        memory_data: MemoryUpdate,
    ) -> Memory:
        """Update memory"""
        # Get existing memory
        memory = await MemoryService.get_memory_by_id(db, memory_id, user_id)
        
        # Verify category if being updated
        if memory_data.category_id:
            result = await db.execute(
                select(Category).where(Category.id == memory_data.category_id)
            )
            if not result.scalar_one_or_none():
                raise NotFoundError("Category not found")
        
        # Update fields
        update_data = memory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(memory, field, value)
        
        await db.commit()
        await db.refresh(memory)
        
        return memory
    
    @staticmethod
    async def delete_memory(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete memory"""
        memory = await MemoryService.get_memory_by_id(db, memory_id, user_id)
        
        await db.delete(memory)
        await db.commit()


    @staticmethod
    async def get_throwback_memory(
        db: AsyncSession,
        user_id: str,
        years_ago: int = 1,
    ) -> Optional[Memory]:
        """
        Get a memory from exactly N years ago (same day and month).
        Returns the most recent memory if multiple exist on that day.
        """
        from datetime import datetime, timedelta
        from sqlalchemy import and_, extract
        
        # Calculate the target date (N years ago, same day and month)
        today = datetime.now()
        target_year = today.year - years_ago
        
        # Find memories created on this day/month N years ago
        query = select(Memory).where(
            and_(
                Memory.user_id == user_id,
                extract('month', Memory.created_at) == today.month,
                extract('day', Memory.created_at) == today.day,
                extract('year', Memory.created_at) == target_year,
            )
        ).order_by(Memory.created_at.desc())
        
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        
        return memory
    
    @staticmethod
    async def get_memory_stats(
        db: AsyncSession,
        memory_id: str,
        user_id: Optional[str] = None,
    ) -> dict:
        """Get statistics for a memory (likes, comments, shares)"""
        # Count reactions (total)
        reactions_count_result = await db.execute(
            select(func.count()).select_from(MemoryReaction).where(
                MemoryReaction.memory_id == memory_id
            )
        )
        reactions_count = reactions_count_result.scalar() or 0
        
        # Count comments
        comments_count_result = await db.execute(
            select(func.count()).select_from(MemoryComment).where(
                MemoryComment.memory_id == memory_id
            )
        )
        comments_count = comments_count_result.scalar() or 0
        
        # Count shares
        shares_count_result = await db.execute(
            select(func.count()).select_from(memory_shares).where(
                memory_shares.c.memory_id == memory_id
            )
        )
        shares_count = shares_count_result.scalar() or 0
        
        # Check if current user reacted
        is_reacted = False
        if user_id:
            reaction_result = await db.execute(
                select(MemoryReaction).where(
                    and_(
                        MemoryReaction.memory_id == memory_id,
                        MemoryReaction.user_id == user_id
                    )
                )
            )
            is_reacted = reaction_result.scalar_one_or_none() is not None
        
        return {
            "reactions_count": reactions_count,
            "comments_count": comments_count,
            "shares_count": shares_count,
            "views_count": shares_count,  # Используем количество шаров как просмотры (пока нет отдельного трекинга)
            "is_reacted": is_reacted,
        }
