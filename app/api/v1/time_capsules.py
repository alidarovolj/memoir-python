"""Time Capsules endpoints"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.time_capsule import CapsuleStatus
from app.schemas.time_capsule import (
    TimeCapsule,
    TimeCapsuleCreate,
    TimeCapsuleUpdate,
    TimeCapsuleList,
)
from app.services.time_capsule_service import TimeCapsuleService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.post("", response_model=TimeCapsule, status_code=status.HTTP_201_CREATED)
async def create_capsule(
    capsule_data: TimeCapsuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new time capsule"""
    try:
        capsule = await TimeCapsuleService.create_capsule(
            db,
            user_id=str(current_user.id),
            capsule_data=capsule_data,
        )
        return capsule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=TimeCapsuleList)
async def get_capsules(
    status_filter: Optional[CapsuleStatus] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of time capsules with pagination"""
    skip = (page - 1) * size
    
    capsules, total = await TimeCapsuleService.get_capsules(
        db,
        user_id=str(current_user.id),
        status=status_filter,
        skip=skip,
        limit=size,
    )
    
    pages = math.ceil(total / size) if total > 0 else 0
    
    return {
        "items": capsules,
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.get("/ready", response_model=list[TimeCapsule])
async def get_ready_capsules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get capsules that are ready to open"""
    capsules = await TimeCapsuleService.get_ready_capsules(
        db,
        user_id=str(current_user.id),
    )
    return capsules


@router.get("/{capsule_id}", response_model=TimeCapsule)
async def get_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get time capsule by ID"""
    try:
        capsule = await TimeCapsuleService.get_capsule_by_id(
            db,
            capsule_id=capsule_id,
            user_id=str(current_user.id),
        )
        return capsule
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time capsule not found",
        )


@router.post("/{capsule_id}/open", response_model=TimeCapsule)
async def open_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open a time capsule (if ready)"""
    try:
        capsule = await TimeCapsuleService.open_capsule(
            db,
            capsule_id=capsule_id,
            user_id=str(current_user.id),
        )
        return capsule
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time capsule not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{capsule_id}", response_model=TimeCapsule)
async def update_capsule(
    capsule_id: str,
    capsule_data: TimeCapsuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update time capsule (only if not opened)"""
    try:
        capsule = await TimeCapsuleService.update_capsule(
            db,
            capsule_id=capsule_id,
            user_id=str(current_user.id),
            capsule_data=capsule_data,
        )
        return capsule
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time capsule not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{capsule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete time capsule"""
    try:
        await TimeCapsuleService.delete_capsule(
            db,
            capsule_id=capsule_id,
            user_id=str(current_user.id),
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time capsule not found",
        )
