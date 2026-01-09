"""Business logic for Task Group operations"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task_group import TaskGroup
from app.schemas.task_group import TaskGroupCreate, TaskGroupUpdate


class TaskGroupService:
    """Service for task group operations"""

    @staticmethod
    async def get_task_groups(
        db: AsyncSession,
        user_id: UUID,
    ) -> tuple[List[TaskGroup], int]:
        """Get user's task groups"""
        query = select(TaskGroup).where(TaskGroup.user_id == user_id)
        query = query.order_by(TaskGroup.order_index.asc(), TaskGroup.created_at.desc())

        result = await db.execute(query)
        groups = result.scalars().all()

        return groups, len(groups)

    @staticmethod
    async def get_task_group_by_id(
        db: AsyncSession,
        group_id: UUID,
        user_id: UUID,
    ) -> Optional[TaskGroup]:
        """Get task group by ID"""
        result = await db.execute(
            select(TaskGroup).where(
                and_(TaskGroup.id == group_id, TaskGroup.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_task_group(
        db: AsyncSession,
        user_id: UUID,
        group_data: TaskGroupCreate,
    ) -> TaskGroup:
        """Create a new task group"""
        group = TaskGroup(
            user_id=user_id,
            name=group_data.name,
            color=group_data.color,
            icon=group_data.icon,
            notification_enabled=group_data.notification_enabled,
            order_index=group_data.order_index,
        )

        db.add(group)
        await db.commit()
        await db.refresh(group)

        return group

    @staticmethod
    async def update_task_group(
        db: AsyncSession,
        group_id: UUID,
        user_id: UUID,
        group_data: TaskGroupUpdate,
    ) -> Optional[TaskGroup]:
        """Update a task group"""
        group = await TaskGroupService.get_task_group_by_id(db, group_id, user_id)
        if not group:
            return None

        # Update fields
        if group_data.name is not None:
            group.name = group_data.name
        if group_data.color is not None:
            group.color = group_data.color
        if group_data.icon is not None:
            group.icon = group_data.icon
        if group_data.notification_enabled is not None:
            group.notification_enabled = group_data.notification_enabled
        if group_data.order_index is not None:
            group.order_index = group_data.order_index

        await db.commit()
        await db.refresh(group)

        return group

    @staticmethod
    async def delete_task_group(
        db: AsyncSession,
        group_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a task group"""
        group = await TaskGroupService.get_task_group_by_id(db, group_id, user_id)
        if not group:
            return False

        await db.delete(group)
        await db.commit()

        return True
