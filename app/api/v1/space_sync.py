"""API endpoints for task space synchronization between friends."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.v1.friends import get_friendship_between_users, user_to_friend_profile
from app.db.session import get_db
from app.models.friendship import Friendship, FriendshipStatus
from app.models.space_sync import SpaceSync, SpaceSyncStatus
from app.models.space_sync_task_invite import (
    SpaceSyncTaskInvite,
    SpaceSyncTaskInviteStatus,
)
from app.models.task import Task, TaskPriority, TaskStatus, TimeScope
from app.models.user import User
from app.schemas.space_sync import (
    SpaceSyncAction,
    SpaceSyncOut,
    SpaceSyncPartnerRemove,
    SpaceSyncPartnersList,
    SpaceSyncRequestCreate,
    SpaceSyncRequestOut,
    SpaceSyncRequestRespond,
    SpaceSyncRequestsList,
    SpaceSyncStatusOut,
    SpaceSyncTaskInviteOut,
    SpaceSyncTaskInviteRespond,
    SpaceSyncTaskInvitesList,
)
from app.schemas.task import TaskListResponse
from app.services.notification_service import NotificationService
from app.services.space_sync_task_service import SpaceSyncTaskService
from app.services.task_service import TaskService

router = APIRouter()


async def get_space_sync_between_users(
    db: AsyncSession, user1_id: UUID, user2_id: UUID
) -> SpaceSync | None:
    result = await db.execute(
        select(SpaceSync).where(
            or_(
                and_(
                    SpaceSync.requester_id == user1_id,
                    SpaceSync.partner_id == user2_id,
                ),
                and_(
                    SpaceSync.requester_id == user2_id,
                    SpaceSync.partner_id == user1_id,
                ),
            )
        )
    )
    return result.scalar_one_or_none()


async def verify_friendship(db: AsyncSession, user1_id: UUID, user2_id: UUID) -> None:
    friendship = await get_friendship_between_users(db, user1_id, user2_id)
    if not friendship or friendship.status != FriendshipStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be friends to sync task spaces",
        )


async def verify_active_sync(
    db: AsyncSession, user1_id: UUID, user2_id: UUID
) -> SpaceSync:
    sync = await get_space_sync_between_users(db, user1_id, user2_id)
    if not sync or sync.status != SpaceSyncStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task spaces are not synced with this user",
        )
    return sync


def sync_to_out(sync: SpaceSync, partner: Optional[User] = None) -> SpaceSyncOut:
    return SpaceSyncOut(
        id=str(sync.id),
        requester_id=str(sync.requester_id),
        partner_id=str(sync.partner_id),
        status=sync.status,
        created_at=sync.created_at,
        updated_at=sync.updated_at,
        partner=None,
        )


def task_to_response_dict(task: Task) -> dict:
    return {
        "id": str(task.id),
        "user_id": str(task.user_id),
        "title": task.title,
        "description": task.description,
        "color": task.color,
        "icon": task.icon,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "scheduled_time": task.scheduled_time,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
        "time_scope": task.time_scope.value
        if hasattr(task.time_scope, "value")
        else task.time_scope,
        "category_id": str(task.category_id) if task.category_id else None,
        "category_name": task.category.name if task.category else None,
        "task_group_id": str(task.task_group_id) if task.task_group_id else None,
        "task_group_name": task.task_group.name if task.task_group else None,
        "task_group_icon": task.task_group.icon if task.task_group else None,
        "related_memory_id": str(task.related_memory_id)
        if task.related_memory_id
        else None,
        "ai_suggested": task.ai_suggested,
        "ai_confidence": task.ai_confidence,
        "tags": task.tags,
        "is_recurring": task.is_recurring,
        "recurrence_rule": task.recurrence_rule,
        "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        "subtasks": [
            {
                "id": str(subtask.id),
                "task_id": str(subtask.task_id),
                "title": subtask.title,
                "is_completed": subtask.is_completed,
                "order": subtask.order,
                "created_at": subtask.created_at.isoformat()
                if subtask.created_at
                else None,
                "updated_at": subtask.updated_at.isoformat()
                if subtask.updated_at
                else None,
                "completed_at": subtask.completed_at.isoformat()
                if subtask.completed_at
                else None,
            }
            for subtask in (task.subtasks or [])
        ],
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


async def notify_sync_event(
    event_type: str,
    sync: SpaceSync,
    actor: User,
    target_user_id: UUID,
    db: AsyncSession,
) -> None:
    from app.api.v1.messages import manager

    actor_name = (
        f"{actor.first_name} {actor.last_name}".strip()
        if (actor.first_name or actor.last_name)
        else (actor.username or "Someone")
    )

    payload = {
        "type": event_type,
        "sync_id": str(sync.id),
        "requester_id": str(sync.requester_id),
        "partner_id": str(sync.partner_id),
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

    target_result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = target_result.scalar_one_or_none()
    if not target_user or not target_user.fcm_token:
        return

    if event_type == "space_sync_request":
        await NotificationService.send_space_sync_request_notification(
            fcm_token=target_user.fcm_token,
            actor_name=actor_name,
            actor_id=str(actor.id),
            sync_id=str(sync.id),
        )
    elif event_type == "space_sync_accepted":
        await NotificationService.send_space_sync_accepted_notification(
            fcm_token=target_user.fcm_token,
            actor_name=actor_name,
            actor_id=str(actor.id),
            sync_id=str(sync.id),
        )


@router.post("/requests", response_model=SpaceSyncAction, status_code=status.HTTP_201_CREATED)
async def send_space_sync_request(
    request: SpaceSyncRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        partner_id = UUID(request.partner_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid partner_id format",
        ) from exc

    if partner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot sync task space with yourself",
        )

    partner_result = await db.execute(select(User).where(User.id == partner_id))
    partner = partner_result.scalar_one_or_none()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await verify_friendship(db, current_user.id, partner_id)

    existing = await get_space_sync_between_users(db, current_user.id, partner_id)
    if existing:
        if existing.status == SpaceSyncStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task spaces are already synced",
            )
        if existing.status == SpaceSyncStatus.PENDING:
            if existing.requester_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sync request already sent",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user already sent you a sync request",
            )
        if existing.requester_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send a new sync request in this direction",
            )
        existing.status = SpaceSyncStatus.PENDING
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        await notify_sync_event("space_sync_request", existing, current_user, partner_id, db)
        return SpaceSyncAction(
            success=True,
            message="Space sync request sent",
            sync=sync_to_out(existing),
        )

    sync = SpaceSync(
        requester_id=current_user.id,
        partner_id=partner_id,
        status=SpaceSyncStatus.PENDING,
    )
    db.add(sync)
    await db.commit()
    await db.refresh(sync)

    await notify_sync_event("space_sync_request", sync, current_user, partner_id, db)

    return SpaceSyncAction(
        success=True,
        message="Space sync request sent",
        sync=sync_to_out(sync),
    )


@router.get("/requests", response_model=SpaceSyncRequestsList)
async def get_incoming_space_sync_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpaceSync)
        .where(
            and_(
                SpaceSync.partner_id == current_user.id,
                SpaceSync.status == SpaceSyncStatus.PENDING,
            )
        )
        .order_by(SpaceSync.created_at.desc())
    )
    syncs = result.scalars().all()

    requests: List[SpaceSyncRequestOut] = []
    for sync in syncs:
        requester_result = await db.execute(
            select(User).where(User.id == sync.requester_id)
        )
        requester = requester_result.scalar_one()
        requests.append(
            SpaceSyncRequestOut(
                id=str(sync.id),
                status=sync.status,
                requester=await user_to_friend_profile(requester, db, current_user.id),
                created_at=sync.created_at,
            )
        )

    return SpaceSyncRequestsList(requests=requests)


@router.get("/requests/sent", response_model=SpaceSyncRequestsList)
async def get_sent_space_sync_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpaceSync)
        .where(
            and_(
                SpaceSync.requester_id == current_user.id,
                SpaceSync.status == SpaceSyncStatus.PENDING,
            )
        )
        .order_by(SpaceSync.created_at.desc())
    )
    syncs = result.scalars().all()

    requests: List[SpaceSyncRequestOut] = []
    for sync in syncs:
        requester_result = await db.execute(
            select(User).where(User.id == sync.requester_id)
        )
        requester = requester_result.scalar_one()
        requests.append(
            SpaceSyncRequestOut(
                id=str(sync.id),
                status=sync.status,
                requester=await user_to_friend_profile(requester, db, current_user.id),
                created_at=sync.created_at,
            )
        )

    return SpaceSyncRequestsList(requests=requests)


@router.post("/requests/respond", response_model=SpaceSyncAction)
async def respond_to_space_sync_request(
    response: SpaceSyncRequestRespond,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        request_id = int(response.request_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request_id format",
        ) from exc

    result = await db.execute(select(SpaceSync).where(SpaceSync.id == request_id))
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync request not found",
        )

    if sync.partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond to requests sent to you",
        )

    if sync.status != SpaceSyncStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sync request is no longer pending",
        )

    if response.action == "accept":
        sync.status = SpaceSyncStatus.ACCEPTED
        message = "Space sync accepted"
        event_type = "space_sync_accepted"
    else:
        sync.status = SpaceSyncStatus.REJECTED
        message = "Space sync rejected"
        event_type = "space_sync_rejected"

    await db.commit()
    await db.refresh(sync)
    if response.action == "accept":
        await SpaceSyncTaskService.backfill_accepted_invites_for_sync(db, sync)
    await notify_sync_event(event_type, sync, current_user, sync.requester_id, db)

    return SpaceSyncAction(
        success=True,
        message=message,
        sync=sync_to_out(sync),
    )


@router.delete("/requests/{request_id}", response_model=SpaceSyncAction)
async def cancel_space_sync_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SpaceSync).where(SpaceSync.id == request_id))
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync request not found",
        )

    if sync.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own sync requests",
        )

    if sync.status != SpaceSyncStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sync request is no longer pending",
        )

    sync.status = SpaceSyncStatus.CANCELLED
    await db.commit()
    await db.refresh(sync)
    await notify_sync_event("space_sync_cancelled", sync, current_user, sync.partner_id, db)

    return SpaceSyncAction(
        success=True,
        message="Space sync request cancelled",
        sync=sync_to_out(sync),
    )


@router.get("/partners", response_model=SpaceSyncPartnersList)
async def get_sync_partners(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpaceSync).where(
            and_(
                or_(
                    SpaceSync.requester_id == current_user.id,
                    SpaceSync.partner_id == current_user.id,
                ),
                SpaceSync.status == SpaceSyncStatus.ACCEPTED,
            )
        )
    )
    syncs = result.scalars().all()

    partners: List = []
    for sync in syncs:
        partner_id = (
            sync.partner_id if sync.requester_id == current_user.id else sync.requester_id
        )
        partner_result = await db.execute(select(User).where(User.id == partner_id))
        partner = partner_result.scalar_one_or_none()
        if partner:
            partners.append(
                await user_to_friend_profile(partner, db, current_user.id)
            )

    return SpaceSyncPartnersList(partners=partners, total=len(partners))


@router.get("/status/{user_id}", response_model=SpaceSyncStatusOut)
async def get_space_sync_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        other_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format",
        ) from exc

    if other_user_id == current_user.id:
        return SpaceSyncStatusOut(status="none")

    sync = await get_space_sync_between_users(db, current_user.id, other_user_id)
    if not sync:
        return SpaceSyncStatusOut(status="none")

    if sync.status == SpaceSyncStatus.ACCEPTED:
        return SpaceSyncStatusOut(status="synced", request_id=str(sync.id))

    if sync.status == SpaceSyncStatus.PENDING:
        if sync.requester_id == current_user.id:
            return SpaceSyncStatusOut(status="pending_sent", request_id=str(sync.id))
        return SpaceSyncStatusOut(status="pending_received", request_id=str(sync.id))

    return SpaceSyncStatusOut(status="none")


@router.get("/task-invites", response_model=SpaceSyncTaskInvitesList)
async def get_pending_task_invites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invites = await SpaceSyncTaskService.get_pending_invites(db, current_user.id)
    items: List[SpaceSyncTaskInviteOut] = []
    for invite in invites:
        if not invite.task or not invite.from_user:
            continue
        items.append(
            SpaceSyncTaskInviteOut(
                id=str(invite.id),
                status=invite.status,
                created_at=invite.created_at,
                from_user=await user_to_friend_profile(
                    invite.from_user, db, current_user.id
                ),
                task=task_to_response_dict(invite.task),
            )
        )
    return SpaceSyncTaskInvitesList(invites=items, total=len(items))


@router.post("/task-invites/respond", response_model=SpaceSyncAction)
async def respond_to_task_invite(
    response: SpaceSyncTaskInviteRespond,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        invite_id = int(response.invite_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite_id format",
        ) from exc

    result = await db.execute(
        select(SpaceSyncTaskInvite).where(SpaceSyncTaskInvite.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task invite not found",
        )

    if invite.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond to invites sent to you",
        )

    if invite.status != SpaceSyncTaskInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task invite is no longer pending",
        )

    invite.status = (
        SpaceSyncTaskInviteStatus.ACCEPTED
        if response.action == "accept"
        else SpaceSyncTaskInviteStatus.REJECTED
    )
    invite.responded_at = datetime.utcnow()
    await db.commit()

    action_label = "accepted" if response.action == "accept" else "rejected"
    return SpaceSyncAction(
        success=True,
        message=f"Task invite {action_label}",
        sync=None,
    )


@router.get("/shared-tasks", response_model=TaskListResponse)
async def get_shared_tasks(
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    time_scope: Optional[TimeScope] = None,
    priority: Optional[TaskPriority] = None,
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    tasks, total = await SpaceSyncTaskService.get_accepted_shared_tasks(
        db=db,
        user_id=current_user.id,
        time_scope=time_scope,
        date=date,
        skip=skip,
        limit=page_size,
    )

    if status_filter:
        tasks = [task for task in tasks if task.status == status_filter]
        total = len(tasks)
    if priority:
        tasks = [task for task in tasks if task.priority == priority]
        total = len(tasks)

    return TaskListResponse(
        items=[task_to_response_dict(task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/partners", response_model=SpaceSyncAction)
async def remove_space_sync(
    body: SpaceSyncPartnerRemove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        partner_id = UUID(body.partner_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid partner_id format",
        ) from exc

    sync = await verify_active_sync(db, current_user.id, partner_id)
    await db.delete(sync)
    await db.commit()

    await notify_sync_event("space_sync_removed", sync, current_user, partner_id, db)

    return SpaceSyncAction(
        success=True,
        message="Space sync removed",
        sync=sync_to_out(sync),
    )


@router.get("/{partner_id}/tasks", response_model=TaskListResponse)
async def get_partner_tasks(
    partner_id: UUID,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    time_scope: Optional[TimeScope] = None,
    priority: Optional[TaskPriority] = None,
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_active_sync(db, current_user.id, partner_id)

    skip = (page - 1) * page_size
    tasks, total = await TaskService.get_tasks(
        db=db,
        user_id=partner_id,
        status=status_filter,
        time_scope=time_scope,
        priority=priority,
        date=date,
        skip=skip,
        limit=page_size,
    )

    return TaskListResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
    )
