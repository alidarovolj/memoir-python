"""Daily Prompt schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class DailyPromptBase(BaseModel):
    """Base daily prompt schema"""
    prompt_text: str = Field(..., description="Question or prompt text")
    prompt_icon: str = Field(..., description="Emoji icon")
    category: str = Field(..., description="MORNING, DAYTIME, EVENING, WEEKLY")
    prompt_type: str = Field(..., description="GRATITUDE, REFLECTION, etc.")


class DailyPromptCreate(DailyPromptBase):
    """Schema for creating a daily prompt (admin only)"""
    is_active: bool = True
    order_index: int = 0


class DailyPromptUpdate(BaseModel):
    """Schema for updating a daily prompt (admin only)"""
    prompt_text: Optional[str] = None
    prompt_icon: Optional[str] = None
    category: Optional[str] = None
    prompt_type: Optional[str] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class DailyPrompt(DailyPromptBase):
    """Full daily prompt schema"""
    id: UUID
    is_active: bool
    order_index: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PromptAnswerCreate(BaseModel):
    """Schema for answering a prompt"""
    prompt_id: UUID = Field(..., description="ID of the prompt being answered")
    answer: str = Field(..., min_length=1, description="User's answer to the prompt")
    
    
class PromptAnswerResponse(BaseModel):
    """Response after answering a prompt"""
    memory_id: UUID = Field(..., description="ID of created memory")
    xp_gained: int = Field(..., description="XP gained from answering")
    message: str = Field(..., description="Success message")
