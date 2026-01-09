from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# Request schemas
class CreateGroupChallengeRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    goal: int = Field(..., gt=0)
    goal_type: str = Field(..., pattern="^(memories|tasks|streak)$")
    start_date: datetime
    end_date: datetime
    max_members: int = Field(default=10, ge=2, le=50)
    is_public: bool = Field(default=False)


class InviteFriendsRequest(BaseModel):
    challenge_id: int
    friend_ids: List[int] = Field(..., min_items=1)


# Response schemas
class GroupChallengeMember(BaseModel):
    user_id: int
    username: str
    progress: int
    completed: bool
    joined_at: datetime
    
    class Config:
        orm_mode = True


class GroupChallengeOut(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    goal: int
    goal_type: str
    start_date: datetime
    end_date: datetime
    max_members: int
    is_public: bool
    created_at: datetime
    members: List[GroupChallengeMember] = []
    members_count: int = 0
    
    class Config:
        orm_mode = True
