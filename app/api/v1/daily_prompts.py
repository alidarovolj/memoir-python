"""Daily Prompts endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.daily_prompt import PromptCategory
from app.schemas.daily_prompt import (
    DailyPrompt,
    DailyPromptCreate,
    DailyPromptUpdate,
    PromptAnswerCreate,
    PromptAnswerResponse,
)
from app.services.daily_prompt_service import DailyPromptService
from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/today", response_model=DailyPrompt)
async def get_prompt_of_the_day(
    category: Optional[PromptCategory] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get daily prompt
    
    Returns a consistent prompt for the day based on the date.
    Optional category filter (MORNING, DAYTIME, EVENING, WEEKLY).
    """
    prompt = await DailyPromptService.get_prompt_of_the_day(db, category=category)
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active prompts available",
        )
    
    return prompt


@router.post("/answer", response_model=PromptAnswerResponse)
async def answer_prompt(
    answer_data: PromptAnswerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Answer a daily prompt
    
    Creates a memory from the answer and awards XP to the user's pet.
    """
    try:
        # Verify prompt exists
        prompt = await DailyPromptService.get_prompt_by_id(
            db,
            prompt_id=str(answer_data.prompt_id),
        )
        
        # Create memory from answer
        memory_data = MemoryCreate(
            title=f"{prompt.prompt_icon} {prompt.prompt_text}",
            content=answer_data.answer,
            category_id=None,  # Can be categorized by AI later
            source_type="manual",
        )
        
        memory = await MemoryService.create_memory(
            db,
            user_id=str(current_user.id),
            memory_data=memory_data,
        )
        
        # Award XP to pet (if user has one)
        xp_gained = 10  # Base XP for answering prompt
        
        # Try to feed pet
        try:
            from app.services.pet_service import PetService
            pet = await PetService.get_user_pet(db, user_id=str(current_user.id))
            if pet:
                await PetService.feed_pet(db, user_id=str(current_user.id))
        except Exception as e:
            print(f"⚠️ Failed to feed pet after prompt answer: {e}")
            # Don't fail the request if pet feeding fails
        
        return {
            "memory_id": memory.id,
            "xp_gained": xp_gained,
            "message": "Отлично! Ваш ответ сохранен 🎉",
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save answer: {str(e)}",
        )


@router.get("", response_model=list[DailyPrompt])
async def get_all_prompts(
    active_only: bool = Query(True, description="Only active prompts"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all daily prompts"""
    prompts = await DailyPromptService.get_all_prompts(db, active_only=active_only)
    return prompts


@router.get("/{prompt_id}", response_model=DailyPrompt)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prompt by ID"""
    try:
        prompt = await DailyPromptService.get_prompt_by_id(db, prompt_id=prompt_id)
        return prompt
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )


# Admin endpoints (TODO: add auth check)
@router.post("", response_model=DailyPrompt, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: DailyPromptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create daily prompt (admin only)"""
    prompt = await DailyPromptService.create_prompt(db, prompt_data=prompt_data)
    return prompt


@router.patch("/{prompt_id}", response_model=DailyPrompt)
async def update_prompt(
    prompt_id: str,
    prompt_data: DailyPromptUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update daily prompt (admin only)"""
    try:
        prompt = await DailyPromptService.update_prompt(
            db,
            prompt_id=prompt_id,
            prompt_data=prompt_data,
        )
        return prompt
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete daily prompt (admin only)"""
    try:
        await DailyPromptService.delete_prompt(db, prompt_id=prompt_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )
