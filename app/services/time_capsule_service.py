"""Time Capsule service"""
from typing import Optional, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.time_capsule import TimeCapsule, CapsuleStatus
from app.schemas.time_capsule import TimeCapsuleCreate, TimeCapsuleUpdate
from app.core.exceptions import NotFoundError, AuthorizationError


class TimeCapsuleService:
    """Time Capsule service"""
    
    @staticmethod
    async def create_capsule(
        db: AsyncSession,
        user_id: str,
        capsule_data: TimeCapsuleCreate,
    ) -> TimeCapsule:
        """Create a new time capsule"""
        # Validate open_date is in the future
        now = datetime.now(timezone.utc)
        if capsule_data.open_date <= now:
            raise ValueError("open_date must be in the future")
        
        capsule = TimeCapsule(
            user_id=user_id,
            title=capsule_data.title,
            content=capsule_data.content,
            open_date=capsule_data.open_date,
            status=CapsuleStatus.SEALED,
        )
        
        db.add(capsule)
        await db.commit()
        await db.refresh(capsule)
        
        return capsule
    
    @staticmethod
    async def get_capsules(
        db: AsyncSession,
        user_id: str,
        status: Optional[CapsuleStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[TimeCapsule], int]:
        """Get list of capsules with optional status filter"""
        # Base query
        query = select(TimeCapsule).where(TimeCapsule.user_id == user_id)
        
        # Filter by status if provided
        if status:
            query = query.where(TimeCapsule.status == status)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(TimeCapsule.open_date.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        capsules = result.scalars().all()
        
        return capsules, total
    
    @staticmethod
    async def get_capsule_by_id(
        db: AsyncSession,
        capsule_id: str,
        user_id: str,
    ) -> TimeCapsule:
        """Get capsule by ID"""
        query = select(TimeCapsule).where(
            and_(
                TimeCapsule.id == capsule_id,
                TimeCapsule.user_id == user_id,
            )
        )
        
        result = await db.execute(query)
        capsule = result.scalar_one_or_none()
        
        if not capsule:
            raise NotFoundError("Time capsule not found")
        
        return capsule
    
    @staticmethod
    async def open_capsule(
        db: AsyncSession,
        capsule_id: str,
        user_id: str,
    ) -> TimeCapsule:
        """Open a time capsule (if ready)"""
        capsule = await TimeCapsuleService.get_capsule_by_id(db, capsule_id, user_id)
        
        # Check if capsule is ready to open
        if not capsule.is_ready_to_open:
            raise ValueError(f"Capsule cannot be opened yet. Wait {capsule.days_until_open} more days.")
        
        # Mark as opened
        capsule.status = CapsuleStatus.OPENED
        capsule.opened_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(capsule)
        
        return capsule
    
    @staticmethod
    async def update_capsule(
        db: AsyncSession,
        capsule_id: str,
        user_id: str,
        capsule_data: TimeCapsuleUpdate,
    ) -> TimeCapsule:
        """Update capsule (only if not opened)"""
        capsule = await TimeCapsuleService.get_capsule_by_id(db, capsule_id, user_id)
        
        # Can only update sealed capsules
        if capsule.status != CapsuleStatus.SEALED:
            raise ValueError("Cannot update an opened capsule")
        
        # Update fields
        update_data = capsule_data.model_dump(exclude_unset=True)
        
        # Validate new open_date if provided
        if "open_date" in update_data:
            now = datetime.now(timezone.utc)
            if update_data["open_date"] <= now:
                raise ValueError("open_date must be in the future")
        
        for field, value in update_data.items():
            setattr(capsule, field, value)
        
        await db.commit()
        await db.refresh(capsule)
        
        return capsule
    
    @staticmethod
    async def delete_capsule(
        db: AsyncSession,
        capsule_id: str,
        user_id: str,
    ) -> None:
        """Delete capsule"""
        capsule = await TimeCapsuleService.get_capsule_by_id(db, capsule_id, user_id)
        
        await db.delete(capsule)
        await db.commit()
    
    @staticmethod
    async def get_ready_capsules(
        db: AsyncSession,
        user_id: str,
    ) -> List[TimeCapsule]:
        """Get capsules that are ready to open"""
        now = datetime.now(timezone.utc)
        
        query = select(TimeCapsule).where(
            and_(
                TimeCapsule.user_id == user_id,
                TimeCapsule.status == CapsuleStatus.SEALED,
                TimeCapsule.open_date <= now,
            )
        ).order_by(TimeCapsule.open_date.asc())
        
        result = await db.execute(query)
        capsules = result.scalars().all()
        
        return capsules
