from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


# Association table for many-to-many relationship between memories and shared users
memory_shares = Table(
    'memory_shares',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('memory_id', UUID(as_uuid=True), ForeignKey('memories.id', ondelete='CASCADE'), nullable=False),
    Column('shared_with_user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('can_comment', Boolean, default=True, nullable=False),
    Column('can_react', Boolean, default=True, nullable=False),
)


class MemoryShareHistory(Base):
    """
    History of memory shares - tracks when and with whom a memory was shared
    """
    __tablename__ = "memory_share_history"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    viewed_at = Column(DateTime, nullable=True)  # When the recipient viewed the memory
    
    # Relationships
    memory = relationship("Memory", backref="share_history")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    
    def __repr__(self):
        return f"<MemoryShareHistory memory_id={self.memory_id} shared_with={self.shared_with_user_id}>"
