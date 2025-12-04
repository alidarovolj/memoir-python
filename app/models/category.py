"""Category model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Category(Base):
    """Category model"""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    icon = Column(String(100), nullable=False)
    color = Column(String(7), nullable=False)  # HEX color
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    memories = relationship("Memory", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"

