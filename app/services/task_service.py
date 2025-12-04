"""Business logic for Task operations"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload

from app.models.task import Task, TaskStatus, TaskPriority, TimeScope
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service for task operations"""

    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        user_id: UUID,
        status: Optional[TaskStatus] = None,
        time_scope: Optional[TimeScope] = None,
        priority: Optional[TaskPriority] = None,
        category_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Task], int]:
        """Get user's tasks with filters"""
        # Build query
        query = select(Task).where(Task.user_id == user_id)

        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if time_scope:
            query = query.where(Task.time_scope == time_scope)
        if priority:
            query = query.where(Task.priority == priority)
        if category_id:
            query = query.where(Task.category_id == category_id)

        # Order by: urgent first, then by due_date, then by created_at
        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nulls_last(),
            Task.created_at.desc()
        )

        # Get total count
        count_query = select(Task).where(Task.user_id == user_id)
        if status:
            count_query = count_query.where(Task.status == status)
        if time_scope:
            count_query = count_query.where(Task.time_scope == time_scope)
        if priority:
            count_query = count_query.where(Task.priority == priority)
        if category_id:
            count_query = count_query.where(Task.category_id == category_id)

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute
        result = await db.execute(query.options(joinedload(Task.category)))
        tasks = result.scalars().all()

        return tasks, total

    @staticmethod
    async def get_task_by_id(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> Optional[Task]:
        """Get task by ID"""
        result = await db.execute(
            select(Task)
            .where(and_(Task.id == task_id, Task.user_id == user_id))
            .options(joinedload(Task.category), joinedload(Task.related_memory))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_task(
        db: AsyncSession,
        user_id: UUID,
        task_data: TaskCreate,
    ) -> Task:
        """Create a new task"""
        task = Task(
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            due_date=task_data.due_date,
            status=task_data.status,
            priority=task_data.priority,
            time_scope=task_data.time_scope,
            category_id=task_data.category_id,
            related_memory_id=task_data.related_memory_id,
            tags=task_data.tags,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
        task_data: TaskUpdate,
    ) -> Optional[Task]:
        """Update a task"""
        task = await TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None

        # Update fields
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def complete_task(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> Optional[Task]:
        """Mark task as completed"""
        task = await TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None

        task.status = TaskStatus.completed
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def delete_task(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a task"""
        task = await TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return False

        await db.delete(task)
        await db.commit()

        return True

    @staticmethod
    async def get_tasks_by_date_range(
        db: AsyncSession,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Task]:
        """Get tasks within a date range"""
        result = await db.execute(
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.due_date >= start_date,
                    Task.due_date <= end_date,
                )
            )
            .options(joinedload(Task.category))
            .order_by(Task.due_date.asc())
        )
        return result.scalars().all()

