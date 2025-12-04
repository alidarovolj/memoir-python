"""Story service"""
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.story import Story
from app.models.memory import Memory
from app.models.user import User
from app.schemas.story import StoryCreate
from app.core.exceptions import NotFoundError, AuthorizationError


class StoryService:
    """Story service"""
    
    @staticmethod
    async def create_story(
        db: AsyncSession,
        user_id: str,
        story_data: StoryCreate,
    ) -> Story:
        """Create a new story"""
        # Verify memory exists and belongs to user
        result = await db.execute(
            select(Memory).where(
                and_(
                    Memory.id == story_data.memory_id,
                    Memory.user_id == user_id
                )
            )
        )
        memory = result.scalar_one_or_none()
        if not memory:
            raise NotFoundError("Memory not found or you don't have access")
        
        # Check if story already exists for this memory
        existing_story = await db.execute(
            select(Story).where(
                and_(
                    Story.memory_id == story_data.memory_id,
                    Story.user_id == user_id
                )
            )
        )
        if existing_story.scalar_one_or_none():
            raise ValueError("Story for this memory already exists")
        
        new_story = Story(
            user_id=user_id,
            memory_id=story_data.memory_id,
            is_public=story_data.is_public,
        )
        
        db.add(new_story)
        await db.commit()
        await db.refresh(new_story)
        
        return new_story
    
    @staticmethod
    async def get_public_stories(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Story], int]:
        """Get public stories that haven't expired"""
        now = datetime.utcnow()
        
        # Base query for public, non-expired stories
        query = select(Story).where(
            and_(
                Story.is_public == True,
                Story.expires_at > now
            )
        ).options(
            selectinload(Story.user),
            selectinload(Story.memory)
        ).order_by(Story.created_at.desc())
        
        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(Story).where(
            and_(
                Story.is_public == True,
                Story.expires_at > now
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        stories = result.scalars().all()
        
        return list(stories), total
    
    @staticmethod
    async def get_user_stories(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Story], int]:
        """Get user's own stories (including private)"""
        query = select(Story).where(
            Story.user_id == user_id
        ).options(
            selectinload(Story.memory)
        ).order_by(Story.created_at.desc())
        
        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(Story).where(
            Story.user_id == user_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        stories = result.scalars().all()
        
        return list(stories), total
    
    @staticmethod
    async def delete_story(
        db: AsyncSession,
        story_id: str,
        user_id: str,
    ) -> None:
        """Delete a story"""
        result = await db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()
        
        if not story:
            raise NotFoundError("Story not found")
        
        if str(story.user_id) != user_id:
            raise AuthorizationError("You can only delete your own stories")
        
        await db.delete(story)
        await db.commit()
    
    @staticmethod
    async def cleanup_expired_stories(db: AsyncSession) -> int:
        """Clean up expired stories (для Celery task)"""
        now = datetime.utcnow()
        result = await db.execute(
            select(Story).where(Story.expires_at <= now)
        )
        expired_stories = result.scalars().all()
        
        count = len(expired_stories)
        for story in expired_stories:
            await db.delete(story)
        
        await db.commit()
        return count

