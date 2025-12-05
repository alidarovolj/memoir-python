"""API endpoints for tasks"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority, TimeScope
from app.schemas.task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskListResponse,
    TaskToMemoryConversion,
)
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = None,
    time_scope: Optional[TimeScope] = None,
    priority: Optional[TaskPriority] = None,
    category_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's tasks with optional filters
    
    **Filters:**
    - status: pending, in_progress, completed, cancelled
    - time_scope: daily, weekly, monthly, long_term
    - priority: low, medium, high, urgent
    - category_id: filter by category
    """
    skip = (page - 1) * page_size
    tasks, total = await TaskService.get_tasks(
        db=db,
        user_id=current_user.id,
        status=status,
        time_scope=time_scope,
        priority=priority,
        category_id=category_id,
        skip=skip,
        limit=page_size,
    )

    # Add category names
    tasks_with_category = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "scheduled_time": task.scheduled_time,
            "completed_at": task.completed_at,
            "status": task.status,
            "priority": task.priority,
            "time_scope": task.time_scope,
            "category_id": task.category_id,
            "category_name": task.category.name if task.category else None,
            "related_memory_id": task.related_memory_id,
            "ai_suggested": task.ai_suggested,
            "ai_confidence": task.ai_confidence,
            "tags": task.tags,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
        tasks_with_category.append(task_dict)

    return {
        "items": tasks_with_category,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get task by ID"""
    task = await TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        **task.__dict__,
        "category_name": task.category.name if task.category else None,
    }


@router.post("", response_model=Task, status_code=201)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new task
    
    **Fields:**
    - title: Task title (required)
    - description: Detailed description
    - due_date: When task should be completed
    - status: pending, in_progress, completed, cancelled
    - priority: low, medium, high, urgent
    - time_scope: daily, weekly, monthly, long_term
    - category_id: Link to category
    - related_memory_id: Link to memory
    - tags: List of tags
    """
    task = await TaskService.create_task(db, current_user.id, task_data)
    
    return {
        **task.__dict__,
        "category_name": task.category.name if task.category else None,
    }


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task"""
    task = await TaskService.update_task(db, task_id, current_user.id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        **task.__dict__,
        "category_name": task.category.name if task.category else None,
    }


@router.post("/{task_id}/complete", response_model=Task)
async def complete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark task as completed
    
    Sets status to 'completed' and records completion timestamp
    """
    task = await TaskService.complete_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        **task.__dict__,
        "category_name": task.category.name if task.category else None,
    }


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task"""
    success = await TaskService.delete_task(db, task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return None


@router.post("/{task_id}/convert-to-memory")
async def convert_task_to_memory(
    task_id: UUID,
    conversion_data: TaskToMemoryConversion,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Convert a completed task to a memory
    
    **Flow:**
    1. Verify task exists and is completed
    2. Create memory with task's content + additional notes
    3. Link memory to task (related_task_id)
    4. Process memory with AI (classification, embeddings)
    
    **Examples:**
    - "Посмотреть Начало" → "Посмотрел Начало"
    - "Прочитать 1984" → "Прочитал 1984"
    - "Сходить в Парк Горького" → "Посетил Парк Горького"
    
    **Request body:**
    - content: Additional content/notes about the completed task
    - rating: Optional rating (0-10) for movies/books
    - notes: Additional thoughts/impressions
    - image_url: Optional image
    - backdrop_url: Optional backdrop
    """
    memory = await TaskService.convert_to_memory(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        conversion_data=conversion_data,
    )
    
    if not memory:
        raise HTTPException(status_code=404, detail="Task not found or not completed")
    
    return memory


@router.post("/{task_id}/generate-instances")
async def generate_recurring_instances(
    task_id: UUID,
    days_ahead: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate recurring task instances for the next N days
    
    **Flow:**
    1. Verify task is recurring (is_recurring=true)
    2. Parse recurrence_rule (RRULE format)
    3. Generate task instances for the next N days
    4. Skip dates that already have instances
    
    **Supported recurrence rules:**
    - `FREQ=DAILY` - Every day
    - `FREQ=WEEKLY` - Every week (same day)
    - `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR` - Weekdays only
    - `FREQ=MONTHLY` - Every month (same day)
    
    **Query params:**
    - days_ahead: Number of days to generate (1-30, default 7)
    
    **Returns:**
    List of created task instances
    
    **Example:**
    ```
    Task: "Почистить зубы"
    - is_recurring: true
    - recurrence_rule: "FREQ=DAILY"
    
    → Creates 7 instances (today to 7 days ahead)
    ```
    """
    instances = await TaskService.generate_recurring_instances(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        days_ahead=days_ahead,
    )
    
    return {
        "parent_task_id": str(task_id),
        "instances_created": len(instances),
        "instances": [
            {
                "id": str(inst.id),
                "title": inst.title,
                "due_date": inst.due_date.isoformat() if inst.due_date else None,
                "status": inst.status.value,
            }
            for inst in instances
        ]
    }

