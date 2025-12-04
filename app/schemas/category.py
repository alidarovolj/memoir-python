"""Category Pydantic schemas"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str
    display_name: str
    icon: str
    color: str


class CategoryCreate(CategoryBase):
    """Category creation schema"""
    pass


class CategoryUpdate(BaseModel):
    """Category update schema"""
    display_name: str | None = None
    icon: str | None = None
    color: str | None = None


class CategoryInDB(CategoryBase):
    """Category in database schema"""
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDB):
    """Category response schema"""
    pass

