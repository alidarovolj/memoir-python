"""Pydantic schemas for messages"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    receiver_id: UUID = Field(..., description="ID of the message receiver")


class MessageOut(MessageBase):
    """Schema for message output"""
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response schema for message list"""
    messages: list[MessageOut]
    total: int
    page: int
    page_size: int


class WebSocketMessage(BaseModel):
    """Schema for WebSocket message"""
    type: str = Field(..., description="Message type: 'send', 'read', 'typing'")
    receiver_id: Optional[UUID] = None
    content: Optional[str] = None
    message_id: Optional[UUID] = None
