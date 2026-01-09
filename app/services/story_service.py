"""Story service"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from app.models.story import Story
from app.models.story_like import StoryLike
from app.models.story_comment import StoryComment
from app.models.story_share import StoryShare
from app.models.memory import Memory
from app.models.user import User
from app.schemas.story import StoryCreate, StoryRepostCreate
from app.schemas.story_comment import StoryCommentCreate, StoryCommentUpdate
from app.schemas.story_share import StoryShareCreate
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
            selectinload(Story.memory),
            selectinload(Story.original_story).selectinload(Story.user)
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
            selectinload(Story.memory),
            selectinload(Story.original_story).selectinload(Story.user)
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
    
    # ==================== LIKES ====================
    
    @staticmethod
    async def like_story(
        db: AsyncSession,
        story_id: str,
        user_id: str,
    ) -> StoryLike:
        """Like a story"""
        # Verify story exists and is public/accessible
        result = await db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise NotFoundError("Story not found")
        
        # Check if already liked
        existing_like = await db.execute(
            select(StoryLike).where(
                and_(
                    StoryLike.story_id == story_id,
                    StoryLike.user_id == user_id
                )
            )
        )
        if existing_like.scalar_one_or_none():
            raise ValueError("Story already liked")
        
        new_like = StoryLike(
            story_id=story_id,
            user_id=user_id,
        )
        
        db.add(new_like)
        await db.commit()
        await db.refresh(new_like)
        
        return new_like
    
    @staticmethod
    async def unlike_story(
        db: AsyncSession,
        story_id: str,
        user_id: str,
    ) -> None:
        """Unlike a story"""
        result = await db.execute(
            select(StoryLike).where(
                and_(
                    StoryLike.story_id == story_id,
                    StoryLike.user_id == user_id
                )
            )
        )
        like = result.scalar_one_or_none()
        
        if not like:
            raise NotFoundError("Like not found")
        
        await db.delete(like)
        await db.commit()
    
    @staticmethod
    async def get_story_likes(
        db: AsyncSession,
        story_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[StoryLike], int]:
        """Get likes for a story"""
        query = select(StoryLike).where(
            StoryLike.story_id == story_id
        ).options(
            selectinload(StoryLike.user)
        ).order_by(StoryLike.created_at.desc())
        
        # Count total
        count_query = select(func.count()).select_from(StoryLike).where(
            StoryLike.story_id == story_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        likes = result.scalars().all()
        
        return list(likes), total
    
    # ==================== COMMENTS ====================
    
    @staticmethod
    async def create_comment(
        db: AsyncSession,
        story_id: str,
        user_id: str,
        comment_data: StoryCommentCreate,
    ) -> StoryComment:
        """Create a comment on a story"""
        # Verify story exists
        result = await db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise NotFoundError("Story not found")
        
        new_comment = StoryComment(
            story_id=story_id,
            user_id=user_id,
            content=comment_data.content,
        )
        
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
        
        return new_comment
    
    @staticmethod
    async def update_comment(
        db: AsyncSession,
        comment_id: str,
        user_id: str,
        comment_data: StoryCommentUpdate,
    ) -> StoryComment:
        """Update a comment"""
        result = await db.execute(
            select(StoryComment).where(StoryComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise NotFoundError("Comment not found")
        
        if str(comment.user_id) != user_id:
            raise AuthorizationError("You can only update your own comments")
        
        comment.content = comment_data.content
        comment.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(comment)
        
        return comment
    
    @staticmethod
    async def delete_comment(
        db: AsyncSession,
        comment_id: str,
        user_id: str,
    ) -> None:
        """Delete a comment"""
        result = await db.execute(
            select(StoryComment).where(StoryComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise NotFoundError("Comment not found")
        
        if str(comment.user_id) != user_id:
            raise AuthorizationError("You can only delete your own comments")
        
        await db.delete(comment)
        await db.commit()
    
    @staticmethod
    async def get_story_comments(
        db: AsyncSession,
        story_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[StoryComment], int]:
        """Get comments for a story"""
        query = select(StoryComment).where(
            StoryComment.story_id == story_id
        ).options(
            selectinload(StoryComment.user)
        ).order_by(StoryComment.created_at.asc())
        
        # Count total
        count_query = select(func.count()).select_from(StoryComment).where(
            StoryComment.story_id == story_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        comments = result.scalars().all()
        
        return list(comments), total
    
    # ==================== SHARES ====================
    
    @staticmethod
    async def share_story(
        db: AsyncSession,
        story_id: str,
        sender_id: str,
        share_data: StoryShareCreate,
    ) -> StoryShare:
        """Share a story with another user"""
        # Verify story exists
        result = await db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise NotFoundError("Story not found")
        
        # Verify recipient exists
        recipient_result = await db.execute(
            select(User).where(User.id == share_data.recipient_id)
        )
        recipient = recipient_result.scalar_one_or_none()
        if not recipient:
            raise NotFoundError("Recipient user not found")
        
        new_share = StoryShare(
            story_id=story_id,
            sender_id=sender_id,
            recipient_id=share_data.recipient_id,
        )
        
        db.add(new_share)
        await db.commit()
        await db.refresh(new_share)
        
        return new_share
    
    @staticmethod
    async def mark_share_as_viewed(
        db: AsyncSession,
        share_id: str,
        user_id: str,
    ) -> StoryShare:
        """Mark a shared story as viewed"""
        result = await db.execute(
            select(StoryShare).where(StoryShare.id == share_id)
        )
        share = result.scalar_one_or_none()
        
        if not share:
            raise NotFoundError("Share not found")
        
        if str(share.recipient_id) != user_id:
            raise AuthorizationError("You can only mark your own shares as viewed")
        
        if not share.viewed_at:
            share.viewed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(share)
        
        return share
    
    @staticmethod
    async def get_received_shares(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[StoryShare], int]:
        """Get stories shared with the user"""
        query = select(StoryShare).where(
            StoryShare.recipient_id == user_id
        ).options(
            selectinload(StoryShare.sender),
            selectinload(StoryShare.story).selectinload(Story.user),
            selectinload(StoryShare.story).selectinload(Story.memory)
        ).order_by(StoryShare.created_at.desc())
        
        # Count total
        count_query = select(func.count()).select_from(StoryShare).where(
            StoryShare.recipient_id == user_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        shares = result.scalars().all()
        
        return list(shares), total
    
    # ==================== REPOSTS ====================
    
    @staticmethod
    async def repost_story(
        db: AsyncSession,
        story_id: str,
        user_id: str,
        repost_data: StoryRepostCreate,
    ) -> Story:
        """Repost a story"""
        # Verify original story exists
        result = await db.execute(
            select(Story).where(Story.id == story_id)
        )
        original_story = result.scalar_one_or_none()
        if not original_story:
            raise NotFoundError("Original story not found")
        
        # Check if user already reposted this story
        existing_repost = await db.execute(
            select(Story).where(
                and_(
                    Story.original_story_id == story_id,
                    Story.user_id == user_id
                )
            )
        )
        if existing_repost.scalar_one_or_none():
            raise ValueError("You have already reposted this story")
        
        # Create repost
        new_repost = Story(
            user_id=user_id,
            memory_id=original_story.memory_id,
            original_story_id=story_id,
            is_public=repost_data.is_public,
        )
        
        db.add(new_repost)
        await db.commit()
        await db.refresh(new_repost)
        
        return new_repost
    
    # ==================== STATS ====================
    
    @staticmethod
    async def get_story_stats(
        db: AsyncSession,
        story_id: str,
        current_user_id: Optional[str] = None,
    ) -> dict:
        """Get statistics for a story"""
        # Count likes
        likes_count_result = await db.execute(
            select(func.count()).select_from(StoryLike).where(
                StoryLike.story_id == story_id
            )
        )
        likes_count = likes_count_result.scalar()
        
        # Count comments
        comments_count_result = await db.execute(
            select(func.count()).select_from(StoryComment).where(
                StoryComment.story_id == story_id
            )
        )
        comments_count = comments_count_result.scalar()
        
        # Count shares
        shares_count_result = await db.execute(
            select(func.count()).select_from(StoryShare).where(
                StoryShare.story_id == story_id
            )
        )
        shares_count = shares_count_result.scalar()
        
        # Count reposts
        reposts_count_result = await db.execute(
            select(func.count()).select_from(Story).where(
                Story.original_story_id == story_id
            )
        )
        reposts_count = reposts_count_result.scalar()
        
        # Check if current user liked
        is_liked = False
        if current_user_id:
            like_result = await db.execute(
                select(StoryLike).where(
                    and_(
                        StoryLike.story_id == story_id,
                        StoryLike.user_id == current_user_id
                    )
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None
        
        return {
            "likes_count": likes_count,
            "comments_count": comments_count,
            "shares_count": shares_count,
            "reposts_count": reposts_count,
            "is_liked": is_liked,
        }
    
    # ==================== CLEANUP ====================
    
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

