"""Category service"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.category import Category
from app.core.exceptions import NotFoundError


class CategoryService:
    """Category service"""
    
    @staticmethod
    async def get_categories(db: AsyncSession) -> List[Category]:
        """Get all categories"""
        result = await db.execute(
            select(Category).order_by(Category.name)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_category_by_id(
        db: AsyncSession,
        category_id: str,
    ) -> Category:
        """Get category by ID"""
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise NotFoundError("Category not found")
        
        return category

