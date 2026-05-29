"""Business logic for sharing individual tasks between synced partners."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.space_sync import SpaceSync, SpaceSyncStatus
from app.models.space_sync_task_invite import (
    SpaceSyncTaskInvite,
    SpaceSyncTaskInviteStatus,
)
from app.models.task import Task, TimeScope
from app.models.user import User
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService


class SpaceSyncTaskService:
    @staticmethod
    async def get_active_sync_partner_ids(
        db: AsyncSession, user_id: UUID
    ) -> List[UUID]:
        result = await db.execute(
            select(SpaceSync).where(
                and_(
                    SpaceSync.status == SpaceSyncStatus.ACCEPTED,
                    or_(
                        SpaceSync.requester_id == user_id,
                        SpaceSync.partner_id == user_id,
                    ),
                )
            )
        )
        syncs = result.scalars().all()
        partner_ids: List[UUID] = []
        for sync in syncs:
            partner_id = (
                sync.partner_id if sync.requester_id == user_id else sync.requester_id
            )
            partner_ids.append(partner_id)
        return partner_ids

    @staticmethod
    async def backfill_accepted_invites_for_sync(
        db: AsyncSession, sync: SpaceSync
    ) -> None:
        """Auto-accept existing tasks when a sync link is accepted."""
        pairs = [
            (sync.requester_id, sync.partner_id),
            (sync.partner_id, sync.requester_id),
        ]
        now = datetime.utcnow()

        for from_user_id, to_user_id in pairs:
            tasks_result = await db.execute(
                select(Task.id).where(Task.user_id == from_user_id)
            )
            task_ids = tasks_result.scalars().all()
            for task_id in task_ids:
                existing = await db.execute(
                    select(SpaceSyncTaskInvite).where(
                        and_(
                            SpaceSyncTaskInvite.task_id == task_id,
                            SpaceSyncTaskInvite.to_user_id == to_user_id,
                        )
                    )
                )
                invite = existing.scalar_one_or_none()
                if invite:
                    if invite.status != SpaceSyncTaskInviteStatus.REJECTED:
                        invite.status = SpaceSyncTaskInviteStatus.ACCEPTED
                        invite.responded_at = now
                    continue

                db.add(
                    SpaceSyncTaskInvite(
                        task_id=task_id,
                        from_user_id=from_user_id,
                        to_user_id=to_user_id,
                        status=SpaceSyncTaskInviteStatus.ACCEPTED,
                        responded_at=now,
                    )
                )

        await db.commit()

    @staticmethod
    async def on_task_created(
        db: AsyncSession, creator_id: UUID, task: Task
    ) -> None:
        """Create pending invites and notify sync partners about a new task."""
        if task.parent_task_id is not None:
            return

        partner_ids = await SpaceSyncTaskService.get_active_sync_partner_ids(
            db, creator_id
        )
        if not partner_ids:
            return

        creator_result = await db.execute(
            select(User).where(User.id == creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        if not creator:
            return

        invites: List[SpaceSyncTaskInvite] = []
        for partner_id in partner_ids:
            existing = await db.execute(
                select(SpaceSyncTaskInvite).where(
                    and_(
                        SpaceSyncTaskInvite.task_id == task.id,
                        SpaceSyncTaskInvite.to_user_id == partner_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            invite = SpaceSyncTaskInvite(
                task_id=task.id,
                from_user_id=creator_id,
                to_user_id=partner_id,
                status=SpaceSyncTaskInviteStatus.PENDING,
            )
            db.add(invite)
            invites.append(invite)

        if not invites:
            return

        await db.commit()
        for invite in invites:
            await db.refresh(invite)
            await SpaceSyncTaskService.notify_task_invite(
                db, invite, task, creator, invite.to_user_id
            )

    @staticmethod
    def _display_name(user: User) -> str:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if full_name:
            return full_name
        return user.username or "Someone"

    @staticmethod
    async def notify_task_invite(
        db: AsyncSession,
        invite: SpaceSyncTaskInvite,
        task: Task,
        actor: User,
        target_user_id: UUID,
    ) -> None:
        from app.api.v1.messages import manager

        actor_name = SpaceSyncTaskService._display_name(actor)
        payload = {
            "type": "space_sync_task_invite",
            "invite_id": str(invite.id),
            "task_id": str(task.id),
            "task_title": task.title,
            "actor": {
                "id": str(actor.id),
                "username": actor.username or "",
                "first_name": actor.first_name,
                "last_name": actor.last_name,
                "avatar_url": getattr(actor, "avatar_url", None),
                "display_name": actor_name,
            },
        }

        await manager.send_personal_message(payload, target_user_id)

        if target_user_id in manager.active_connections:
            return

        target_result = await db.execute(
            select(User).where(User.id == target_user_id)
        )
        target_user = target_result.scalar_one_or_none()
        if not target_user or not target_user.fcm_token:
            return

        await NotificationService.send_space_sync_task_invite_notification(
            fcm_token=target_user.fcm_token,
            actor_name=actor_name,
            actor_id=str(actor.id),
            invite_id=str(invite.id),
            task_id=str(task.id),
            task_title=task.title,
        )

    @staticmethod
    async def get_pending_invites(
        db: AsyncSession, user_id: UUID
    ) -> List[SpaceSyncTaskInvite]:
        result = await db.execute(
            select(SpaceSyncTaskInvite)
            .where(
                and_(
                    SpaceSyncTaskInvite.to_user_id == user_id,
                    SpaceSyncTaskInvite.status == SpaceSyncTaskInviteStatus.PENDING,
                )
            )
            .options(
                joinedload(SpaceSyncTaskInvite.task).selectinload(Task.subtasks),
                joinedload(SpaceSyncTaskInvite.from_user),
            )
            .order_by(SpaceSyncTaskInvite.created_at.desc())
        )
        return list(result.scalars().unique().all())

    @staticmethod
    async def get_accepted_shared_tasks(
        db: AsyncSession,
        user_id: UUID,
        time_scope: Optional[TimeScope] = None,
        date: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Task], int]:
        query = (
            select(Task)
            .join(
                SpaceSyncTaskInvite,
                and_(
                    SpaceSyncTaskInvite.task_id == Task.id,
                    SpaceSyncTaskInvite.to_user_id == user_id,
                    SpaceSyncTaskInvite.status == SpaceSyncTaskInviteStatus.ACCEPTED,
                ),
            )
            .options(
                joinedload(Task.category),
                selectinload(Task.task_group),
                selectinload(Task.subtasks),
            )
        )

        if time_scope:
            query = query.where(Task.time_scope == time_scope)

        if date:
            query = query.where(TaskService._due_date_filter(date))

        count_result = await db.execute(query)
        total = len(count_result.scalars().unique().all())

        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        tasks = list(result.scalars().unique().all())
        return tasks, total
