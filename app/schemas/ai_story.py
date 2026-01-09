"""AI Story Generation schemas"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class StoryGenerationRequest(BaseModel):
    """Request for story generation"""
    story_type: Literal["poem", "haiku", "story", "letter", "gratitude"] = Field(
        ..., description="Type of story to generate"
    )
    memory_id: Optional[str] = Field(None, description="Specific memory ID to transform")
    custom_prompt: Optional[str] = Field(None, description="Additional instructions")


class StoryGenerationResponse(BaseModel):
    """Response with generated story"""
    story_type: str
    generated_text: str
    source_memory_id: Optional[str]
    tokens_used: int


class ChatMessage(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant"]
    content: str


class ChatWithPastRequest(BaseModel):
    """Request for chat with past self"""
    message: str = Field(..., description="User's message to past self")
    conversation_history: Optional[List[ChatMessage]] = Field(
        None, description="Previous messages in conversation"
    )


class ChatWithPastResponse(BaseModel):
    """Response from past self"""
    response: str
    tokens_used: int


class YearSummaryRequest(BaseModel):
    """Request for year summary"""
    year: Optional[int] = Field(None, description="Year to summarize (defaults to current)")


class YearSummaryResponse(BaseModel):
    """Year in review summary"""
    year: int
    summary: str
    memories_count: int
    tokens_used: int
