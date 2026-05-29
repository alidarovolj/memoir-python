"""Pydantic schemas for messages"""
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.message import MessageType


class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(default="", max_length=5000, description="Message content or caption")
    message_type: MessageType = Field(default=MessageType.TEXT)
    media_url: Optional[str] = Field(default=None, max_length=2048)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    receiver_id: UUID = Field(..., description="ID of the message receiver")

    @model_validator(mode="after")
    def validate_message_payload(self):
        if self.message_type == MessageType.TEXT:
            if not self.content.strip():
                raise ValueError("content is required for text messages")
        elif not self.media_url:
            raise ValueError("media_url is required for media messages")
        return self


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
    type: str = Field(..., description="Message type: 'send', 'read', 'typing', 'friend_request_send'")
    receiver_id: Optional[UUID] = None
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None
    message_id: Optional[UUID] = None
    addressee_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_ws_send_payload(self):
        if self.type != "send":
            return self
        if self.message_type == MessageType.TEXT:
            if not self.content or not self.content.strip():
                raise ValueError("content is required for text messages")
        elif not self.media_url:
            raise ValueError("media_url is required for media messages")
        return self
