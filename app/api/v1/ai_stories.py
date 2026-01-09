"""AI Story Generation API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai_story import (
    StoryGenerationRequest,
    StoryGenerationResponse,
    ChatWithPastRequest,
    ChatWithPastResponse,
    YearSummaryRequest,
    YearSummaryResponse,
)
from app.services.ai_story_service import AIStoryService

router = APIRouter()


@router.post("/generate-story", response_model=StoryGenerationResponse)
async def generate_story(
    request: StoryGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate creative story from user's memories
    
    Types:
    - poem: Лирическое стихотворение
    - haiku: Хайку (5-7-5)
    - story: Короткий рассказ
    - letter: Письмо будущему себе
    - gratitude: Текст благодарности
    """
    service = AIStoryService()
    
    try:
        result = await service.generate_story(
            db=db,
            user_id=str(current_user.id),
            story_type=request.story_type,
            memory_id=request.memory_id,
            custom_prompt=request.custom_prompt,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story generation failed: {str(e)}",
        )


@router.post("/chat-with-past", response_model=ChatWithPastResponse)
async def chat_with_past(
    request: ChatWithPastRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat with past self based on memories
    AI acts as past version of user
    """
    service = AIStoryService()
    
    try:
        # Convert Pydantic models to dicts for service
        history = None
        if request.conversation_history:
            history = [msg.dict() for msg in request.conversation_history]
        
        result = await service.chat_with_past(
            db=db,
            user_id=str(current_user.id),
            user_message=request.message,
            conversation_history=history,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.post("/year-summary", response_model=YearSummaryResponse)
async def generate_year_summary(
    request: YearSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate year in review summary
    Beautiful overview of user's year based on memories
    """
    service = AIStoryService()
    
    try:
        result = await service.generate_year_summary(
            db=db,
            user_id=str(current_user.id),
            year=request.year,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Year summary failed: {str(e)}",
        )
