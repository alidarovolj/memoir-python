"""Search endpoints"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.memory import Memory
from app.services.search_service import SearchService

router = APIRouter()


@router.get("", response_model=List[Memory])
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search memories using text search"""
    memories = await SearchService.text_search(
        db,
        user_id=str(current_user.id),
        query=q,
        limit=limit,
    )
    return memories


@router.post("/semantic", response_model=List[Memory])
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Semantic search using embeddings"""
    memories = await SearchService.semantic_search(
        db,
        user_id=str(current_user.id),
        query=q,
        limit=limit,
    )
    return memories
