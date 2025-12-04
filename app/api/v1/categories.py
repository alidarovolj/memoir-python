"""Categories endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.category import Category
from app.schemas.memory import MemoryList
from app.services.category_service import CategoryService
from app.services.memory_service import MemoryService
from app.core.exceptions import NotFoundError
import math

router = APIRouter()


@router.get("", response_model=List[Category])
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """Get list of categories"""
    categories = await CategoryService.get_categories(db)
    return categories


@router.get("/{category_id}/memories", response_model=MemoryList)
async def get_category_memories(
    category_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get memories for a category"""
    # Verify category exists
    try:
        await CategoryService.get_category_by_id(db, category_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    skip = (page - 1) * size
    
    memories, total = await MemoryService.get_memories(
        db,
        user_id=str(current_user.id),
        category_id=category_id,
        skip=skip,
        limit=size,
    )
    
    pages = math.ceil(total / size) if total > 0 else 0
    
    return {
        "items": memories,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
