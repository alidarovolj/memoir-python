"""Story API endpoints"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.story import Story, StoryCreate, StoryWithDetails, StoryList
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
    
    # Format response with user and memory details
    stories_with_details = []
    for story in stories:
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
            },
            "memory": {
                "id": str(story.memory.id),
                "title": story.memory.title,
                "content": story.memory.content[:200] + "..." if len(story.memory.content) > 200 else story.memory.content,
                "image_url": story.memory.image_url,
                "backdrop_url": story.memory.backdrop_url,
                "source_type": story.memory.source_type,
            }
        }
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
    
    # Format response with memory details
    stories_with_details = []
    for story in stories:
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
            },
            "memory": {
                "id": str(story.memory.id),
                "title": story.memory.title,
                "content": story.memory.content[:200] + "..." if len(story.memory.content) > 200 else story.memory.content,
                "image_url": story.memory.image_url,
                "backdrop_url": story.memory.backdrop_url,
                "source_type": story.memory.source_type,
            }
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

