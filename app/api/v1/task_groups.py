"""API endpoints for task groups"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.task_group import (
    TaskGroup,
    TaskGroupCreate,
    TaskGroupUpdate,
    TaskGroupListResponse,
)
from app.services.task_group_service import TaskGroupService

router = APIRouter()


@router.get("", response_model=TaskGroupListResponse)
async def get_task_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's task groups
    """
    groups, total = await TaskGroupService.get_task_groups(
        db=db,
        user_id=current_user.id,
    )

    return {
        "items": groups,
        "total": total,
    }


@router.get("/{group_id}", response_model=TaskGroup)
async def get_task_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get task group by ID"""
    group = await TaskGroupService.get_task_group_by_id(db, group_id, current_user.id)
    if not group:
        raise HTTPException(status_code=404, detail="Task group not found")

    return group


@router.post("", response_model=TaskGroup, status_code=201)
async def create_task_group(
    group_data: TaskGroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new task group
    
    **Fields:**
    - name: Group name (required)
    - color: HEX color (required, e.g. #FF5722)
    - icon: Icon identifier (required, e.g. 📋)
    - notification_enabled: Notification setting (default: "none")
    - order_index: Display order (default: 0)
    """
    group = await TaskGroupService.create_task_group(db, current_user.id, group_data)
    return group


@router.put("/{group_id}", response_model=TaskGroup)
async def update_task_group(
    group_id: UUID,
    group_data: TaskGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task group"""
    group = await TaskGroupService.update_task_group(
        db, group_id, current_user.id, group_data
    )
    if not group:
        raise HTTPException(status_code=404, detail="Task group not found")

    return group


@router.delete("/{group_id}", status_code=204)
async def delete_task_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task group"""
    success = await TaskGroupService.delete_task_group(db, group_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Task group not found")

    return None
