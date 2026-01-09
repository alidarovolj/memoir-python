"""Search service for semantic search"""
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.models.memory import Memory
from app.models.embedding import Embedding
from app.services.ai_service import ai_service


class SearchService:
    """Search service"""
    
    @staticmethod
    async def semantic_search(
        db: AsyncSession,
        user_id: str,
        query: str,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> List[Memory]:
        """
        Perform semantic search using embeddings
        
        Args:
            db: Database session
            user_id: User ID to filter memories
            query: Search query
            limit: Maximum results
            threshold: Maximum cosine distance (0-1, lower is more similar)
        
        Returns:
            List of matching memories
        """
        # Generate embedding for query
        query_embedding = await ai_service.generate_embedding(query)
        
        # Perform vector similarity search
        # Using cosine distance via pgvector (<=> operator)
        # Distance of 0 means identical, distance of 1 means completely different
        sql = text("""
            SELECT m.id, e.embedding <=> CAST(:query_embedding AS vector) as distance
            FROM memories m
            JOIN embeddings e ON m.id = e.memory_id
            WHERE m.user_id = :user_id
            AND e.embedding <=> CAST(:query_embedding AS vector) < :threshold
            ORDER BY distance
            LIMIT :limit
        """)
        
        result = await db.execute(
            sql,
            {
                "user_id": user_id,
                "query_embedding": str(query_embedding),
                "threshold": threshold,
                "limit": limit,
            }
        )
        
        rows = result.fetchall()
        memory_ids = [str(row[0]) for row in rows]
        
        # Fetch full memory objects
        if not memory_ids:
            return []
        
        # Preserve the order from the semantic search
        id_to_order = {str(row[0]): idx for idx, row in enumerate(rows)}
        
        query = select(Memory).where(Memory.id.in_(memory_ids))
        query = query.options(selectinload(Memory.category))
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        # Sort by original order
        memories_sorted = sorted(memories, key=lambda m: id_to_order.get(str(m.id), 999))
        
        return list(memories_sorted)
    
    @staticmethod
    async def text_search(
        db: AsyncSession,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> List[Memory]:
        """
        Perform text-based search
        
        Args:
            db: Database session
            user_id: User ID to filter memories
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching memories
        """
        search_query = select(Memory).where(
            Memory.user_id == user_id
        ).where(
            Memory.title.ilike(f"%{query}%") | Memory.content.ilike(f"%{query}%")
        ).options(selectinload(Memory.category))
        
        search_query = search_query.order_by(Memory.created_at.desc())
        search_query = search_query.limit(limit)
        
        result = await db.execute(search_query)
        memories = result.scalars().all()
        
        return list(memories)

