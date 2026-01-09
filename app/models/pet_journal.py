"""Pet journal models - Track pet's growth and memories"""
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class JournalEntryType(str, enum.Enum):
    """Types of journal entries"""
    EVOLUTION = "evolution"
    MILESTONE = "milestone"
    PHOTO = "photo"
    ACHIEVEMENT = "achievement"


class PetJournalEntry(Base):
    """
    Pet journal entry -記録 pet's journey
    """
    __tablename__ = "pet_journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False)
    entry_type = Column(SQLEnum(JournalEntryType), nullable=False)
    
    # Entry content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Metadata
    level_at_time = Column(Integer, nullable=True)
    evolution_stage_at_time = Column(String(50), nullable=True)
    created_at = Column(String(100), server_default=func.now())
    
    # Relationship
    pet = relationship("Pet")
    
    def __repr__(self):
        return f"<PetJournalEntry {self.entry_type} for pet={self.pet_id}>"
