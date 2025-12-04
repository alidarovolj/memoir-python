"""Embedding model for semantic search"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class Embedding(Base):
    """Embedding model for storing vector embeddings"""
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Vector embedding (1536 dimensions for text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=False)
    model = Column(String(100), nullable=False, default="text-embedding-3-small")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    memory = relationship("Memory", back_populates="embedding")

    def __repr__(self):
        return f"<Embedding for memory {self.memory_id}>"

