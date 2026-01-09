"""Daily Prompt model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.base import Base


class PromptCategory(str, enum.Enum):
    """Category of daily prompt"""
    MORNING = "MORNING"      # Утренние промпты (благодарность, намерения)
    DAYTIME = "DAYTIME"      # Дневные промпты (прогресс, моменты)
    EVENING = "EVENING"      # Вечерние промпты (рефлексия, итоги дня)
    WEEKLY = "WEEKLY"        # Еженедельные промпты (цели, достижения)


class PromptType(str, enum.Enum):
    """Type of prompt"""
    GRATITUDE = "GRATITUDE"      # Благодарность
    REFLECTION = "REFLECTION"    # Рефлексия
    LEARNING = "LEARNING"        # Обучение
    GOAL = "GOAL"               # Цели
    EMOTION = "EMOTION"         # Эмоции
    CREATIVITY = "CREATIVITY"    # Креатив


class DailyPrompt(Base):
    """
    Daily Prompt - ежедневные вопросы для рефлексии
    Помогает пользователям легче начать писать
    """
    __tablename__ = "daily_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content
    prompt_text = Column(Text, nullable=False)  # "За что вы благодарны сегодня?"
    prompt_icon = Column(String(10), nullable=False)  # Emoji icon
    
    # Classification
    category = Column(SQLEnum(PromptCategory), nullable=False)
    prompt_type = Column(SQLEnum(PromptType), nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)  # Порядок показа
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<DailyPrompt {self.id} - {self.prompt_text[:50]}>"
