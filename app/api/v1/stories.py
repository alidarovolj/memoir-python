"""Story API endpoints"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.story import Story, StoryCreate, StoryWithDetails, StoryList, StoryRepostCreate
from app.schemas.story_like import StoryLike, StoryLikeWithUser
from app.schemas.story_comment import (
    StoryComment,
    StoryCommentCreate,
    StoryCommentUpdate,
    StoryCommentWithUser,
    StoryCommentList,
)
from app.schemas.story_share import StoryShare, StoryShareCreate, StoryShareWithDetails, StoryShareList
from app.services.story_service import StoryService
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=Story, status_code=status.HTTP_201_CREATED)
async def create_story(
    story_data: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Создать историю из воспоминания
    """
    try:
        story = await StoryService.create_story(
            db=db,
            user_id=str(current_user.id),
            story_data=story_data,
        )
        logger.info(f"Story {story.id} created by user {current_user.id}")
        return story
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=StoryList)
async def get_public_stories(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список публичных историй
    """
    stories, total = await StoryService.get_public_stories(
        db=db,
        skip=skip,
        limit=limit,
    )
    
    # Format response with user and memory details + stats
    stories_with_details = []
    for story in stories:
        # Get stats
        stats = await StoryService.get_story_stats(
            db=db,
            story_id=str(story.id),
            current_user_id=str(current_user.id),
        )
        
        story_dict = {
            "id": story.id,
            "user_id": story.user_id,
            "memory_id": story.memory_id,
            "is_public": story.is_public,
            "created_at": story.created_at,
            "expires_at": story.expires_at,
            "user": {
                "id": str(story.user.id),
                "username": story.user.username,
                "email": story.user.email,
                "first_name": story.user.first_name,
                "last_name": story.user.last_name,
                "avatar_url": story.user.avatar_url,
            },
            "memory": {
                "id": str(story.memory.id),
                "title": story.memory.title,
                "content": story.memory.content[:200] + "..." if len(story.memory.content) > 200 else story.memory.content,
                "image_url": story.memory.image_url,
                "backdrop_url": story.memory.backdrop_url,
                "source_type": story.memory.source_type,
            },
            **stats,  # likes_count, comments_count, shares_count, reposts_count, is_liked
        }
        
        # Add original story info if this is a repost
        if story.original_story_id:
            try:
                if story.original_story and story.original_story.user:
                    story_dict["original_story"] = {
                        "id": str(story.original_story.id),
                        "user": {
                            "id": str(story.original_story.user.id),
                            "username": story.original_story.user.username,
                            "first_name": story.original_story.user.first_name,
                            "last_name": story.original_story.user.last_name,
                            "avatar_url": story.original_story.user.avatar_url,
                        },
                    }
            except Exception as e:
                logger.warning(f"Could not load original story {story.original_story_id}: {e}")
        
        stories_with_details.append(story_dict)
    
    return {"items": stories_with_details, "total": total}


@router.get("/my", response_model=StoryList)
async def get_my_stories(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить свои истории (включая приватные)
    """
    stories, total = await StoryService.get_user_stories(
        db=db,
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )
    
    # Format response with memory details + stats
    stories_with_details = []
    for story in stories:
        # Get stats
        stats = await StoryService.get_story_stats(
            db=db,
            story_id=str(story.id),
            current_user_id=str(current_user.id),
        )
        
        story_dict = {
            "id": story.id,
            "user_id": story.user_id,
            "memory_id": story.memory_id,
            "is_public": story.is_public,
            "created_at": story.created_at,
            "expires_at": story.expires_at,
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "avatar_url": current_user.avatar_url,
            },
            "memory": {
                "id": str(story.memory.id),
                "title": story.memory.title,
                "content": story.memory.content[:200] + "..." if len(story.memory.content) > 200 else story.memory.content,
                "image_url": story.memory.image_url,
                "backdrop_url": story.memory.backdrop_url,
                "source_type": story.memory.source_type,
            },
            **stats,  # likes_count, comments_count, shares_count, reposts_count, is_liked
        }
        stories_with_details.append(story_dict)
    
    return {"items": stories_with_details, "total": total}


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Удалить историю
    """
    try:
        await StoryService.delete_story(
            db=db,
            story_id=story_id,
            user_id=str(current_user.id),
        )
        logger.info(f"Story {story_id} deleted by user {current_user.id}")
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== LIKES ====================

@router.post("/{story_id}/like", response_model=StoryLike, status_code=status.HTTP_201_CREATED)
async def like_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Лайкнуть историю
    """
    try:
        like = await StoryService.like_story(
            db=db,
            story_id=story_id,
            user_id=str(current_user.id),
        )
        logger.info(f"Story {story_id} liked by user {current_user.id}")
        return like
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{story_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Убрать лайк с истории
    """
    try:
        await StoryService.unlike_story(
            db=db,
            story_id=story_id,
            user_id=str(current_user.id),
        )
        logger.info(f"Story {story_id} unliked by user {current_user.id}")
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{story_id}/likes")
async def get_story_likes(
    story_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список лайков истории
    """
    likes, total = await StoryService.get_story_likes(
        db=db,
        story_id=story_id,
        skip=skip,
        limit=limit,
    )
    
    # Format with user details
    likes_with_users = []
    for like in likes:
        like_dict = {
            "id": like.id,
            "story_id": like.story_id,
            "user_id": like.user_id,
            "created_at": like.created_at,
            "user": {
                "id": str(like.user.id),
                "username": like.user.username,
                "first_name": like.user.first_name,
                "last_name": like.user.last_name,
                "avatar_url": like.user.avatar_url,
            }
        }
        likes_with_users.append(like_dict)
    
    return {"items": likes_with_users, "total": total}


# ==================== COMMENTS ====================

@router.post("/{story_id}/comments", response_model=StoryCommentWithUser, status_code=status.HTTP_201_CREATED)
async def create_comment(
    story_id: str,
    comment_data: StoryCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Создать комментарий к истории
    """
    try:
        comment = await StoryService.create_comment(
            db=db,
            story_id=story_id,
            user_id=str(current_user.id),
            comment_data=comment_data,
        )
        
        # Reload to get user relationship
        await db.refresh(comment, ["user"])
        
        return {
            "id": comment.id,
            "story_id": comment.story_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user": {
                "id": str(comment.user.id),
                "username": comment.user.username,
                "first_name": comment.user.first_name,
                "last_name": comment.user.last_name,
                "avatar_url": comment.user.avatar_url,
            }
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{story_id}/comments", response_model=StoryCommentList)
async def get_story_comments(
    story_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить комментарии истории
    """
    comments, total = await StoryService.get_story_comments(
        db=db,
        story_id=story_id,
        skip=skip,
        limit=limit,
    )
    
    # Format with user details
    comments_with_users = []
    for comment in comments:
        comment_dict = {
            "id": comment.id,
            "story_id": comment.story_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user": {
                "id": str(comment.user.id),
                "username": comment.user.username,
                "first_name": comment.user.first_name,
                "last_name": comment.user.last_name,
                "avatar_url": comment.user.avatar_url,
            }
        }
        comments_with_users.append(comment_dict)
    
    return {"items": comments_with_users, "total": total}


@router.put("/comments/{comment_id}", response_model=StoryCommentWithUser)
async def update_comment(
    comment_id: str,
    comment_data: StoryCommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Обновить комментарий
    """
    try:
        comment = await StoryService.update_comment(
            db=db,
            comment_id=comment_id,
            user_id=str(current_user.id),
            comment_data=comment_data,
        )
        
        # Reload to get user relationship
        await db.refresh(comment, ["user"])
        
        return {
            "id": comment.id,
            "story_id": comment.story_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user": {
                "id": str(comment.user.id),
                "username": comment.user.username,
                "first_name": comment.user.first_name,
                "last_name": comment.user.last_name,
                "avatar_url": comment.user.avatar_url,
            }
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Удалить комментарий
    """
    try:
        await StoryService.delete_comment(
            db=db,
            comment_id=comment_id,
            user_id=str(current_user.id),
        )
        logger.info(f"Comment {comment_id} deleted by user {current_user.id}")
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== SHARES ====================

@router.post("/{story_id}/share", response_model=StoryShare, status_code=status.HTTP_201_CREATED)
async def share_story(
    story_id: str,
    share_data: StoryShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Отправить историю другому пользователю
    """
    try:
        share = await StoryService.share_story(
            db=db,
            story_id=story_id,
            sender_id=str(current_user.id),
            share_data=share_data,
        )
        logger.info(f"Story {story_id} shared to user {share_data.recipient_id} by user {current_user.id}")
        return share
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/shared/received", response_model=StoryShareList)
async def get_received_shares(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить истории, отправленные вам
    """
    shares, total = await StoryService.get_received_shares(
        db=db,
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )
    
    # Format with details
    shares_with_details = []
    for share in shares:
        share_dict = {
            "id": share.id,
            "story_id": share.story_id,
            "sender_id": share.sender_id,
            "recipient_id": share.recipient_id,
            "created_at": share.created_at,
            "viewed_at": share.viewed_at,
            "sender": {
                "id": str(share.sender.id),
                "username": share.sender.username,
                "first_name": share.sender.first_name,
                "last_name": share.sender.last_name,
                "avatar_url": share.sender.avatar_url,
            },
            "recipient": {
                "id": str(current_user.id),
                "username": current_user.username,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "avatar_url": current_user.avatar_url,
            },
            "story": {
                "id": str(share.story.id),
                "user": {
                    "id": str(share.story.user.id),
                    "username": share.story.user.username,
                    "first_name": share.story.user.first_name,
                    "last_name": share.story.user.last_name,
                    "avatar_url": share.story.user.avatar_url,
                },
                "memory": {
                    "id": str(share.story.memory.id),
                    "title": share.story.memory.title,
                    "content": share.story.memory.content[:200] + "..." if len(share.story.memory.content) > 200 else share.story.memory.content,
                    "image_url": share.story.memory.image_url,
                    "backdrop_url": share.story.memory.backdrop_url,
                }
            }
        }
        shares_with_details.append(share_dict)
    
    return {"items": shares_with_details, "total": total}


@router.put("/shared/{share_id}/view", response_model=StoryShare)
async def mark_share_as_viewed(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Отметить отправленную историю как просмотренную
    """
    try:
        share = await StoryService.mark_share_as_viewed(
            db=db,
            share_id=share_id,
            user_id=str(current_user.id),
        )
        return share
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== REPOSTS ====================

@router.post("/{story_id}/repost", response_model=Story, status_code=status.HTTP_201_CREATED)
async def repost_story(
    story_id: str,
    repost_data: StoryRepostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Репостнуть историю
    """
    try:
        repost = await StoryService.repost_story(
            db=db,
            story_id=story_id,
            user_id=str(current_user.id),
            repost_data=repost_data,
        )
        logger.info(f"Story {story_id} reposted by user {current_user.id}")
        return repost
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

