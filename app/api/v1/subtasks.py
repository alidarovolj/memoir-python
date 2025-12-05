"""Subtasks API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.subtask import Subtask
from app.schemas.subtask import (
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskInDB,
    SubtaskReorder,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.post("", response_model=SubtaskInDB, status_code=201)
async def create_subtask(
    task_id: UUID,
    subtask_data: SubtaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new subtask for a task
    
    **Request body:**
    - title: Subtask title (required)
    - is_completed: Whether it's completed (default: false)
    - order: Order for sorting (default: 0)
    
    **Example:**
    ```json
    {
      "title": "Собрать материалы",
      "is_completed": false,
      "order": 0
    }
    ```
    """
    # Verify task exists and belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create subtask
    subtask = Subtask(
        task_id=task_id,
        title=subtask_data.title,
        is_completed=subtask_data.is_completed,
        order=subtask_data.order,
    )
    
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    
    return subtask


@router.get("", response_model=List[SubtaskInDB])
async def get_subtasks(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all subtasks for a task
    
    Returns subtasks ordered by `order` field (for drag & drop)
    """
    # Verify task belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get subtasks
    subtasks_query = select(Subtask).where(
        Subtask.task_id == task_id
    ).order_by(Subtask.order)
    
    subtasks_result = await db.execute(subtasks_query)
    subtasks = subtasks_result.scalars().all()
    
    return subtasks


@router.patch("/{subtask_id}", response_model=SubtaskInDB)
async def update_subtask(
    task_id: UUID,
    subtask_id: UUID,
    subtask_data: SubtaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a subtask
    
    **Request body (all optional):**
    - title: New title
    - is_completed: Toggle completion
    - order: New order
    
    **Example:**
    ```json
    {
      "is_completed": true
    }
    ```
    """
    # Verify task belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get subtask
    subtask_query = select(Subtask).where(
        and_(Subtask.id == subtask_id, Subtask.task_id == task_id)
    )
    subtask_result = await db.execute(subtask_query)
    subtask = subtask_result.scalar_one_or_none()
    
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    # Update fields
    if subtask_data.title is not None:
        subtask.title = subtask_data.title
    
    if subtask_data.is_completed is not None:
        subtask.is_completed = subtask_data.is_completed
        if subtask_data.is_completed:
            subtask.completed_at = datetime.utcnow()
        else:
            subtask.completed_at = None
    
    if subtask_data.order is not None:
        subtask.order = subtask_data.order
    
    subtask.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(subtask)
    
    return subtask


@router.delete("/{subtask_id}", status_code=204)
async def delete_subtask(
    task_id: UUID,
    subtask_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a subtask"""
    # Verify task belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get subtask
    subtask_query = select(Subtask).where(
        and_(Subtask.id == subtask_id, Subtask.task_id == task_id)
    )
    subtask_result = await db.execute(subtask_query)
    subtask = subtask_result.scalar_one_or_none()
    
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    await db.delete(subtask)
    await db.commit()
    
    return None


@router.post("/reorder", status_code=200)
async def reorder_subtasks(
    task_id: UUID,
    reorder_data: List[SubtaskReorder],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reorder subtasks (for drag & drop)
    
    **Request body:**
    ```json
    [
      {"subtask_id": "uuid-1", "new_order": 0},
      {"subtask_id": "uuid-2", "new_order": 1},
      {"subtask_id": "uuid-3", "new_order": 2}
    ]
    ```
    """
    # Verify task belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update orders
    for item in reorder_data:
        subtask_query = select(Subtask).where(
            and_(Subtask.id == item.subtask_id, Subtask.task_id == task_id)
        )
        subtask_result = await db.execute(subtask_query)
        subtask = subtask_result.scalar_one_or_none()
        
        if subtask:
            subtask.order = item.new_order
            subtask.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Subtasks reordered successfully"}

