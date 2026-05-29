from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.models.space_sync import SpaceSyncStatus
from app.models.space_sync_task_invite import SpaceSyncTaskInviteStatus
from app.schemas.friendship import FriendProfile


class SpaceSyncRequestCreate(BaseModel):
    partner_id: str = Field(..., description="Friend user ID to sync tasks with")


class SpaceSyncRequestRespond(BaseModel):
    request_id: str = Field(..., description="Space sync request ID")
    action: str = Field(..., description="Action: 'accept' or 'reject'")

    @validator("action")
    def validate_action(cls, value: str) -> str:
        if value not in {"accept", "reject"}:
            raise ValueError('action must be "accept" or "reject"')
        return value


class SpaceSyncPartnerRemove(BaseModel):
    partner_id: str = Field(..., description="Partner user ID to stop syncing with")


class SpaceSyncOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requester_id: str
    partner_id: str
    status: SpaceSyncStatus
    created_at: datetime
    updated_at: datetime
    partner: Optional[FriendProfile] = None


class SpaceSyncRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: SpaceSyncStatus
    requester: FriendProfile
    created_at: datetime


class SpaceSyncRequestsList(BaseModel):
    requests: List[SpaceSyncRequestOut]


class SpaceSyncPartnersList(BaseModel):
    partners: List[FriendProfile]
    total: int


class SpaceSyncStatusOut(BaseModel):
    status: str
    request_id: Optional[str] = None


class SpaceSyncAction(BaseModel):
    success: bool
    message: str
    sync: Optional[SpaceSyncOut] = None


class SpaceSyncTaskInviteRespond(BaseModel):
    invite_id: str = Field(..., description="Task invite ID")
    action: str = Field(..., description="Action: 'accept' or 'reject'")

    @validator("action")
    def validate_action(cls, value: str) -> str:
        if value not in {"accept", "reject"}:
            raise ValueError('action must be "accept" or "reject"')
        return value


class SpaceSyncTaskInviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: SpaceSyncTaskInviteStatus
    created_at: datetime
    from_user: FriendProfile
    task: dict


class SpaceSyncTaskInvitesList(BaseModel):
    invites: List[SpaceSyncTaskInviteOut]
    total: int
