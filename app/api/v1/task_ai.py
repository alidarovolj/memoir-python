"""AI endpoints for tasks"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.task_ai_service import TaskAIService

router = APIRouter()


class TaskAnalysisRequest(BaseModel):
    """Request for task analysis"""
    title: str


class TaskAnalysisResponse(BaseModel):
    """Response with AI analysis"""
    time_scope: str
    priority: str
    category: str | None
    confidence: float
    reasoning: str


@router.post("/analyze", response_model=TaskAnalysisResponse)
async def analyze_task(
    request: TaskAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze task title and suggest time_scope, priority, and category
    
    **Examples:**
    - "Почистить зубы" → daily, medium
    - "Посмотреть Начало" → weekly, medium, movies
    - "Выучить английский" → long_term, high
    """
    ai_service = TaskAIService()
    result = await ai_service.analyze_task(request.title)
    
    return result

