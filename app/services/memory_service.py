"""Memory service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.models.memory import Memory
from app.models.category import Category
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.core.exceptions import NotFoundError, AuthorizationError


class MemoryService:
    """Memory service"""
    
    @staticmethod
    async def create_memory(
        db: AsyncSession, 
        user_id: str, 
        memory_data: MemoryCreate
    ) -> Memory:
        """Create a new memory"""
        # Verify category exists if provided
        if memory_data.category_id:
            result = await db.execute(
                select(Category).where(Category.id == memory_data.category_id)
            )
            if not result.scalar_one_or_none():
                raise NotFoundError("Category not found")
        
        new_memory = Memory(
            user_id=user_id,
            title=memory_data.title,
            content=memory_data.content,
            source_type=memory_data.source_type,
            source_url=memory_data.source_url,
            image_url=memory_data.image_url,
            backdrop_url=memory_data.backdrop_url,
            memory_metadata=memory_data.memory_metadata or {},
            category_id=memory_data.category_id,
        )
        
        print(f"✅ [SERVICE] Memory object created with image_url: {new_memory.image_url}")
        
        db.add(new_memory)
        await db.commit()
        await db.refresh(new_memory)
        
        print(f"✅ [SERVICE] Memory saved to DB with ID: {new_memory.id}")
        print(f"   - image_url: {new_memory.image_url}")
        print(f"   - backdrop_url: {new_memory.backdrop_url}")
        
        return new_memory
    
    @staticmethod
    async def get_memories(
        db: AsyncSession,
        user_id: str,
        category_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Memory], int]:
        """Get paginated list of memories"""
        # Build base query
        query = select(Memory).where(Memory.user_id == user_id)
        
        # Filter by category if provided
        if category_id:
            query = query.where(Memory.category_id == category_id)
        
        # Get total count
        count_query = select(func.count()).select_from(Memory).where(Memory.user_id == user_id)
        if category_id:
            count_query = count_query.where(Memory.category_id == category_id)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.options(selectinload(Memory.category))
        query = query.order_by(Memory.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return list(memories), total
    
    @staticmethod
    async def get_memory_by_id(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> Memory:
        """Get memory by ID"""
        query = select(Memory).where(
            and_(Memory.id == memory_id, Memory.user_id == user_id)
        ).options(selectinload(Memory.category))
        
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise NotFoundError("Memory not found")
        
        return memory
    
    @staticmethod
    async def update_memory(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
        memory_data: MemoryUpdate,
    ) -> Memory:
        """Update memory"""
        # Get existing memory
        memory = await MemoryService.get_memory_by_id(db, memory_id, user_id)
        
        # Verify category if being updated
        if memory_data.category_id:
            result = await db.execute(
                select(Category).where(Category.id == memory_data.category_id)
            )
            if not result.scalar_one_or_none():
                raise NotFoundError("Category not found")
        
        # Update fields
        update_data = memory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(memory, field, value)
        
        await db.commit()
        await db.refresh(memory)
        
        return memory
    
    @staticmethod
    async def delete_memory(
        db: AsyncSession,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete memory"""
        memory = await MemoryService.get_memory_by_id(db, memory_id, user_id)
        
        await db.delete(memory)
        await db.commit()

