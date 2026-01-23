"""API endpoints for tasks"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.task import Task as TaskModel, TaskStatus, TaskPriority, TimeScope
from app.schemas.task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskListResponse,
    TaskToMemoryConversion,
)
from app.services.task_service import TaskService

router = APIRouter()


class SubtaskData(BaseModel):
    """Data for a subtask in habit creation"""
    title: str
    description: str | None = None
    priority: str
    suggested_time: str | None = None
    color: str | None = None
    icon: str | None = None
    is_recurring: bool = True


class CreateHabitRequest(BaseModel):
    """Request to create a habit with group and subtasks"""
    habit_name: str
    group_icon: str
    subtasks: List[SubtaskData]


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = None,
    time_scope: Optional[TimeScope] = None,
    priority: Optional[TaskPriority] = None,
    category_id: Optional[UUID] = None,
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
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
    - date: specific date to filter tasks (YYYY-MM-DD format)
    """
    skip = (page - 1) * page_size
    tasks, total = await TaskService.get_tasks(
        db=db,
        user_id=current_user.id,
        status=status,
        time_scope=time_scope,
        priority=priority,
        category_id=category_id,
        date=date,
        skip=skip,
        limit=page_size,
    )

    # Add category names and task group info
    tasks_with_category = []
    for task in tasks:
        # Для экземпляров повторяющихся задач берем подзадачи из родительской задачи
        subtasks_to_include = task.subtasks
        if task.parent_task_id:
            # Если это экземпляр повторяющейся задачи, всегда загружаем подзадачи из родительской задачи
            parent_task_query = select(TaskModel).where(
                TaskModel.id == task.parent_task_id
            )
            parent_result = await db.execute(
                parent_task_query.options(selectinload(TaskModel.subtasks))
            )
            parent_task = parent_result.scalar_one_or_none()
            if parent_task:
                if parent_task.subtasks:
                    subtasks_to_include = parent_task.subtasks
                    print(f"✅ [TASKS] Loaded {len(subtasks_to_include)} subtasks from parent task {task.parent_task_id} for instance {task.id}")
                    for st in subtasks_to_include:
                        print(f"   - Subtask: {st.title} (completed: {st.is_completed})")
                else:
                    print(f"⚠️ [TASKS] Parent task {task.parent_task_id} has no subtasks for instance {task.id}")
            else:
                print(f"❌ [TASKS] Parent task {task.parent_task_id} not found for instance {task.id}")
        else:
            # Для обычных задач используем их собственные подзадачи
            if task.subtasks:
                print(f"📝 [TASKS] Task {task.id} ({task.title}) has {len(task.subtasks)} own subtasks")
                for st in task.subtasks:
                    print(f"   - Subtask: {st.title} (completed: {st.is_completed})")
        
        task_dict = {
            "id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "description": task.description,
            "color": task.color,
            "icon": task.icon,
            "due_date": task.due_date,
            "scheduled_time": task.scheduled_time,
            "completed_at": task.completed_at,
            "status": task.status,
            "priority": task.priority,
            "time_scope": task.time_scope,
            "category_id": task.category_id,
            "category_name": task.category.name if task.category else None,
            "task_group_id": str(task.task_group_id) if task.task_group_id else None,
            "task_group_name": task.task_group.name if task.task_group else None,
            "task_group_icon": task.task_group.icon if task.task_group else None,
            "related_memory_id": task.related_memory_id,
            "ai_suggested": task.ai_suggested,
            "ai_confidence": task.ai_confidence,
            "tags": task.tags,
            "is_recurring": task.is_recurring,
            "recurrence_rule": task.recurrence_rule,
            "parent_task_id": task.parent_task_id,
            "subtasks": [
                {
                    "id": str(subtask.id),
                    "task_id": str(subtask.task_id),
                    "title": subtask.title,
                    "is_completed": subtask.is_completed,
                    "order": subtask.order,
                    "created_at": subtask.created_at.isoformat() if subtask.created_at else None,
                    "updated_at": subtask.updated_at.isoformat() if subtask.updated_at else None,
                    "completed_at": subtask.completed_at.isoformat() if subtask.completed_at else None,
                }
                for subtask in subtasks_to_include
            ],
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


@router.post("/create-habit")
async def create_habit_with_subtasks(
    request: CreateHabitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a habit (goal) with a task group and multiple subtasks
    
    **Flow:**
    1. Create a task group with the habit name and icon
    2. Create all subtasks and link them to the group
    3. Generate recurring instances for each subtask (7 days ahead)
    
    **Example request:**
    ```json
    {
      "habit_name": "Бросить курить",
      "group_icon": "🚭",
      "subtasks": [
        {
          "title": "Выпить стакан воды",
          "description": "Помогает снизить тягу",
          "priority": "medium",
          "suggested_time": "08:00",
          "color": "#3B82F6",
          "icon": "Ionicons.water_outline",
          "is_recurring": true
        }
      ]
    }
    ```
    
    **Returns:**
    - group_id: ID созданной группы
    - subtasks_created: Количество созданных подзадач
    - subtasks: Список созданных подзадач с их ID
    """
    from app.models.task_group import TaskGroup
    from datetime import datetime, timezone
    
    # 1. Create task group
    task_group = TaskGroup(
        user_id=current_user.id,
        name=request.habit_name,
        icon=request.group_icon,
        color="#6366F1",  # Default primary color
    )
    db.add(task_group)
    await db.flush()  # Get group ID
    
    created_subtasks = []
    
    # 2. Create all subtasks
    for subtask_data in request.subtasks:
        # Parse priority
        priority_map = {
            "low": TaskPriority.low,
            "medium": TaskPriority.medium,
            "high": TaskPriority.high,
            "urgent": TaskPriority.urgent,
        }
        priority = priority_map.get(subtask_data.priority.lower(), TaskPriority.medium)
        
        # Calculate due_date with time from scheduled_time
        # If scheduled_time is provided (e.g., "08:00"), combine with today's date
        # Otherwise, use end of today (23:59)
        now = datetime.now(timezone.utc)
        if subtask_data.suggested_time:
            try:
                hour, minute = map(int, subtask_data.suggested_time.split(':'))
                due_date = datetime(now.year, now.month, now.day, hour, minute, tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                # If parsing fails, use end of day
                due_date = datetime(now.year, now.month, now.day, 23, 59, tzinfo=timezone.utc)
        else:
            # No scheduled time, use end of day
            due_date = datetime(now.year, now.month, now.day, 23, 59, tzinfo=timezone.utc)
        
        # Create TaskCreate schema
        task_create = TaskCreate(
            title=subtask_data.title,
            description=subtask_data.description,
            priority=priority,
            time_scope=TimeScope.daily,  # Habits are usually daily
            status=TaskStatus.pending,
            due_date=due_date,
            scheduled_time=subtask_data.suggested_time,  # Already a string "HH:MM"
            task_group_id=task_group.id,
            is_recurring=subtask_data.is_recurring,
            recurrence_rule="FREQ=DAILY" if subtask_data.is_recurring else None,
            color=subtask_data.color,
            icon=subtask_data.icon,
        )
        
        # Create task
        task = await TaskService.create_task(
            db=db,
            user_id=current_user.id,
            task_data=task_create,
        )
        
        # Generate recurring instances if recurring
        if subtask_data.is_recurring:
            await TaskService.generate_recurring_instances(
                db=db,
                task_id=task.id,
                user_id=current_user.id,
                days_ahead=7,
            )
        
        created_subtasks.append({
            "id": str(task.id),
            "title": task.title,
            "priority": task.priority.value,
            "is_recurring": task.is_recurring,
        })
    
    await db.commit()
    
    return {
        "group_id": str(task_group.id),
        "group_name": task_group.name,
        "group_icon": task_group.icon,
        "subtasks_created": len(created_subtasks),
        "subtasks": created_subtasks,
    }

