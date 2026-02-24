"""Subtasks API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.subtask import Subtask
from app.models.subtask_completion import SubtaskCompletion
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
    
    Returns subtasks ordered by `order` field (for drag & drop).
    For recurring instances, returns parent's subtasks with is_completed
    from subtask_completions (per day).
    """
    # Verify task belongs to user
    task_query = select(Task).where(
        and_(Task.id == task_id, Task.user_id == current_user.id)
    )
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # For instances, load subtasks from parent
    effective_task_id = task.parent_task_id if task.parent_task_id else task_id
    subtasks_query = select(Subtask).where(
        Subtask.task_id == effective_task_id
    ).order_by(Subtask.order)
    
    subtasks_result = await db.execute(subtasks_query)
    subtasks = subtasks_result.scalars().all()
    
    if not subtasks:
        return []
    
    # For instances, override is_completed from subtask_completions
    if task.parent_task_id:
        completions_query = select(SubtaskCompletion).where(
            and_(
                SubtaskCompletion.task_id == task_id,
                SubtaskCompletion.subtask_id.in_([s.id for s in subtasks]),
            )
        )
        completions_result = await db.execute(completions_query)
        completions = {c.subtask_id: c for c in completions_result.scalars().all()}
        # Return parent's subtasks with is_completed from subtask_completions
        # task_id in response = instance id (for PATCH compatibility)
        return [
            SubtaskInDB(
                id=s.id,
                task_id=task_id,
                title=s.title,
                is_completed=s.id in completions,
                order=s.order,
                created_at=s.created_at,
                updated_at=s.updated_at,
                completed_at=completions[s.id].completed_at if s.id in completions else None,
            )
            for s in subtasks
        ]
    
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
    
    For recurring instances (task.parent_task_id), is_completed is stored
    per instance in subtask_completions, not on the parent's Subtask.
    
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
    
    # For instances, subtask belongs to parent
    effective_task_id = task.parent_task_id if task.parent_task_id else task_id
    subtask_query = select(Subtask).where(
        and_(Subtask.id == subtask_id, Subtask.task_id == effective_task_id)
    )
    subtask_result = await db.execute(subtask_query)
    subtask = subtask_result.scalar_one_or_none()
    
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    if task.parent_task_id:
        # Instance: use subtask_completions, do not modify Subtask
        if subtask_data.title is not None or subtask_data.order is not None:
            raise HTTPException(
                status_code=400,
                detail="Title and order can only be edited on the parent task",
            )
        if subtask_data.is_completed is None:
            raise HTTPException(status_code=400, detail="is_completed required for instance update")
        
        now = datetime.now(timezone.utc)
        completion_query = select(SubtaskCompletion).where(
            and_(
                SubtaskCompletion.task_id == task_id,
                SubtaskCompletion.subtask_id == subtask_id,
            )
        )
        completion_result = await db.execute(completion_query)
        completion = completion_result.scalar_one_or_none()
        
        if subtask_data.is_completed:
            if completion:
                completion.completed_at = now
            else:
                completion = SubtaskCompletion(
                    task_id=task_id,
                    subtask_id=subtask_id,
                    completed_at=now,
                )
                db.add(completion)
            completed_at_val = now
        else:
            if completion:
                await db.delete(completion)
            completed_at_val = None
        
        await db.commit()
        return SubtaskInDB(
            id=subtask.id,
            task_id=task_id,
            title=subtask.title,
            is_completed=subtask_data.is_completed,
            order=subtask.order,
            created_at=subtask.created_at,
            updated_at=subtask.updated_at,
            completed_at=completed_at_val,
        )
    
    # Regular task: update Subtask directly
    if subtask_data.title is not None:
        subtask.title = subtask_data.title
    if subtask_data.is_completed is not None:
        subtask.is_completed = subtask_data.is_completed
        if subtask_data.is_completed:
            subtask.completed_at = datetime.now(timezone.utc)
        else:
            subtask.completed_at = None
    if subtask_data.order is not None:
        subtask.order = subtask_data.order
    subtask.updated_at = datetime.now(timezone.utc)
    
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

