"""Daily Prompt service"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import random

from app.models.daily_prompt import DailyPrompt, PromptCategory
from app.schemas.daily_prompt import DailyPromptCreate, DailyPromptUpdate
from app.core.exceptions import NotFoundError


class DailyPromptService:
    """Daily Prompt service"""
    
    @staticmethod
    async def create_prompt(
        db: AsyncSession,
        prompt_data: DailyPromptCreate,
    ) -> DailyPrompt:
        """Create a new daily prompt (admin only)"""
        prompt = DailyPrompt(
            prompt_text=prompt_data.prompt_text,
            prompt_icon=prompt_data.prompt_icon,
            category=prompt_data.category,
            prompt_type=prompt_data.prompt_type,
            is_active=prompt_data.is_active,
            order_index=prompt_data.order_index,
        )
        
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)
        
        return prompt
    
    @staticmethod
    async def get_all_prompts(
        db: AsyncSession,
        active_only: bool = True,
    ) -> List[DailyPrompt]:
        """Get all prompts"""
        query = select(DailyPrompt)
        
        if active_only:
            query = query.where(DailyPrompt.is_active == True)
        
        query = query.order_by(DailyPrompt.order_index.asc())
        result = await db.execute(query)
        prompts = result.scalars().all()
        
        return list(prompts)
    
    @staticmethod
    async def get_prompt_of_the_day(
        db: AsyncSession,
        category: Optional[PromptCategory] = None,
    ) -> Optional[DailyPrompt]:
        """
        Get prompt of the day
        
        Logic:
        - If category specified, filter by category
        - Select random prompt from active prompts
        - Use date as seed for consistent daily prompt
        """
        query = select(DailyPrompt).where(DailyPrompt.is_active == True)
        
        if category:
            query = query.where(DailyPrompt.category == category)
        
        query = query.order_by(DailyPrompt.order_index.asc())
        result = await db.execute(query)
        prompts = result.scalars().all()
        
        if not prompts:
            return None
        
        # Use current date as seed for consistent daily selection
        today = datetime.now(timezone.utc).date()
        seed = int(today.strftime("%Y%m%d"))
        random.seed(seed)
        
        # Select random prompt
        selected_prompt = random.choice(prompts)
        
        return selected_prompt
    
    @staticmethod
    async def get_prompt_by_id(
        db: AsyncSession,
        prompt_id: str,
    ) -> DailyPrompt:
        """Get prompt by ID"""
        query = select(DailyPrompt).where(DailyPrompt.id == prompt_id)
        result = await db.execute(query)
        prompt = result.scalar_one_or_none()
        
        if not prompt:
            raise NotFoundError("Daily prompt not found")
        
        return prompt
    
    @staticmethod
    async def update_prompt(
        db: AsyncSession,
        prompt_id: str,
        prompt_data: DailyPromptUpdate,
    ) -> DailyPrompt:
        """Update daily prompt (admin only)"""
        prompt = await DailyPromptService.get_prompt_by_id(db, prompt_id)
        
        update_data = prompt_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prompt, field, value)
        
        await db.commit()
        await db.refresh(prompt)
        
        return prompt
    
    @staticmethod
    async def delete_prompt(
        db: AsyncSession,
        prompt_id: str,
    ) -> None:
        """Delete daily prompt (admin only)"""
        prompt = await DailyPromptService.get_prompt_by_id(db, prompt_id)
        
        await db.delete(prompt)
        await db.commit()
