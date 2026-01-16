"""User Pydantic schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreatePhone(BaseModel):
    """User creation schema via Phone + Firebase"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    firebase_token: str = Field(..., min_length=10)  # ID token from Firebase
    username: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None


class UserInDB(UserBase):
    """User in database schema"""
    id: UUID
    firebase_uid: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """User response schema"""
    pass

