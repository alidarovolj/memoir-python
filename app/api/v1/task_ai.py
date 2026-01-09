"""AI endpoints for tasks"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.memory import Memory
from app.services.task_ai_service import TaskAIService

router = APIRouter()


class TaskAnalysisRequest(BaseModel):
    """Request for task analysis"""
    title: str


class TaskAnalysisResponse(BaseModel):
    """Response with AI analysis"""
    time_scope: str
    priority: str
    suggested_time: str | None = None  # Format: "HH:MM"
    needs_deadline: bool = False
    is_recurring: bool = False
    category: str | None
    confidence: float
    reasoning: str


class TaskSuggestion(BaseModel):
    """AI-suggested task"""
    title: str
    description: str
    time_scope: str
    priority: str
    confidence: float
    reasoning: str
    category: str | None = None


class HabitAnalysisRequest(BaseModel):
    """Request for habit analysis"""
    title: str  # e.g., "Бросить курить", "Начать бегать"


class SubtaskSuggestion(BaseModel):
    """Suggested subtask for a habit"""
    title: str
    description: str | None = None
    priority: str
    suggested_time: str | None = None  # Format: "HH:MM"
    color: str  # Hex color
    icon: str  # Ionicons name
    is_recurring: bool = True  # Most habit subtasks are daily


class HabitAnalysisResponse(BaseModel):
    """Response with habit analysis and suggested subtasks"""
    group_name: str  # e.g., "Бросить курить"
    group_icon: str  # Emoji for the group
    subtasks: List[SubtaskSuggestion]
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


@router.post("/memories/{memory_id}/suggest-tasks", response_model=List[TaskSuggestion])
async def suggest_tasks_from_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI предлагает задачи на основе воспоминания
    
    **Examples:**
    - Память "Посмотрел Начало" → ["Посмотреть Интерстеллар", "Посмотреть Престиж"]
    - Память "Прочитал 1984" → ["Прочитать Скотный двор", "Прочитать О дивный новый мир"]
    
    **Returns:**
    - Список из 2-3 предложенных задач
    - Каждая с title, description, priority, time_scope, confidence
    """
    # Получаем воспоминание
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    stmt = select(Memory).where(
        Memory.id == memory_id,
        Memory.user_id == current_user.id
    ).options(selectinload(Memory.category))
    
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Получаем AI suggestions
    ai_service = TaskAIService()
    suggestions = await ai_service.suggest_tasks_from_memory(memory, limit=3)
    
    return suggestions


@router.post("/analyze-habit", response_model=HabitAnalysisResponse)
async def analyze_habit(
    request: HabitAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze habit/goal and generate suggested subtasks
    
    **Examples:**
    - "Бросить курить" → ["Выпить воды", "Использовать пластырь", "Сделать упражнение"]
    - "Начать бегать" → ["Утренняя пробежка", "Растяжка", "Выпить воды"]
    - "Похудеть" → ["Здоровый завтрак", "Тренировка", "Прогулка"]
    
    **Returns:**
    - Название группы
    - Иконка группы (emoji)
    - Список подзадач (4-6 штук)
    - Каждая подзадача с title, description, priority, suggested_time, color, icon
    """
    ai_service = TaskAIService()
    result = await ai_service.analyze_habit(request.title)
    
    return result

