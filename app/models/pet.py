"""
Pet model - Virtual companion for user engagement and retention
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class PetType(str, enum.Enum):
    """Available pet types"""
    BIRD = "BIRD"
    CAT = "CAT"
    DRAGON = "DRAGON"
    FOX = "FOX"          # Лиса - хитрая и умная
    PANDA = "PANDA"      # Панда - милая и ленивая
    UNICORN = "UNICORN"  # Единорог - магический и редкий
    RABBIT = "RABBIT"    # Кролик - быстрый и энергичный
    OWL = "OWL"          # Сова - мудрая и ночная


class EvolutionStage(str, enum.Enum):
    """Pet evolution stages"""
    EGG = "EGG"      # 0-4 levels
    BABY = "BABY"    # 5-14 levels
    CHILD = "CHILD"  # 15-24 levels (НОВАЯ СТАДИЯ)
    ADULT = "ADULT"  # 25-39 levels
    LEGEND = "LEGEND"  # 40+ levels


class Pet(Base):
    """
    Virtual pet companion that grows with user activity
    
    Mechanics:
    - Creating memories = feeding (increases happiness)
    - Completing tasks = playing (increases health)
    - Daily streak = keeps pet healthy
    - Evolution happens at levels: 5, 15, 30
    """
    __tablename__ = "pets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Pet identity
    pet_type = Column(SQLEnum(PetType), nullable=False, default=PetType.BIRD)
    name = Column(String(50), nullable=False)  # User-given name
    
    # Progression system
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    evolution_stage = Column(SQLEnum(EvolutionStage), default=EvolutionStage.EGG, nullable=False)
    
    # Pet stats (0-100)
    happiness = Column(Integer, default=100, nullable=False)  # Decreases if no memories created
    health = Column(Integer, default=100, nullable=False)     # Decreases if no tasks completed
    
    # Timestamps
    last_fed = Column(DateTime(timezone=True), server_default=func.now())      # Last memory created
    last_played = Column(DateTime(timezone=True), server_default=func.now())   # Last task completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Customization
    accessories = Column(String(500), default="{}")  # JSON string of unlocked items
    
    # Mutations & Special
    is_shiny = Column(Boolean, default=False, nullable=False)  # Редкая версия (5% шанс)
    mutation_type = Column(String(50), nullable=True)  # sparkle, aura, glow, rainbow
    special_effect = Column(String(100), nullable=True)  # Доп эффекты
    
    # Relationship
    user = relationship("User", back_populates="pet")

    def __repr__(self):
        return f"<Pet {self.name} (Level {self.level}, {self.pet_type})>"

    @property
    def xp_for_next_level(self) -> int:
        """Calculate XP needed for next level (exponential growth)"""
        return 100 + (self.level * 50)
    
    @property
    def evolution_level(self) -> int:
        """Get current evolution level based on stage"""
        stages = {
            EvolutionStage.EGG: 0,
            EvolutionStage.BABY: 1,
            EvolutionStage.ADULT: 2,
            EvolutionStage.LEGEND: 3,
        }
        return stages.get(self.evolution_stage, 0)
    
    def can_evolve(self) -> bool:
        """Check if pet is ready to evolve"""
        evolution_thresholds = {
            EvolutionStage.EGG: 5,      # Evolve to baby at level 5
            EvolutionStage.BABY: 15,    # Evolve to child at level 15
            EvolutionStage.CHILD: 25,   # Evolve to adult at level 25
            EvolutionStage.ADULT: 40,   # Evolve to legend at level 40
        }
        
        threshold = evolution_thresholds.get(self.evolution_stage)
        if threshold and self.level >= threshold:
            return True
        return False
    
    def evolve(self) -> bool:
        """Evolve pet to next stage if possible"""
        if not self.can_evolve():
            return False
        
        evolution_map = {
            EvolutionStage.EGG: EvolutionStage.BABY,
            EvolutionStage.BABY: EvolutionStage.CHILD,
            EvolutionStage.CHILD: EvolutionStage.ADULT,
            EvolutionStage.ADULT: EvolutionStage.LEGEND,
        }
        
        next_stage = evolution_map.get(self.evolution_stage)
        if next_stage:
            self.evolution_stage = next_stage
            return True
        return False
    
    def add_xp(self, amount: int) -> dict:
        """
        Add XP and handle level ups
        Returns dict with level_up and evolution flags
        """
        self.xp += amount
        level_ups = 0
        
        # Check for level ups
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            level_ups += 1
        
        # Check for evolution
        evolved = False
        if self.can_evolve():
            evolved = self.evolve()
        
        return {
            "level_ups": level_ups,
            "evolved": evolved,
            "current_level": self.level,
            "current_stage": self.evolution_stage.value,
        }
    
    def feed(self, xp_amount: int = 10) -> dict:
        """
        Feed pet (create memory action)
        Increases happiness and gives XP
        """
        self.happiness = min(100, self.happiness + 10)
        self.last_fed = func.now()
        return self.add_xp(xp_amount)
    
    def play(self, xp_amount: int = 15) -> dict:
        """
        Play with pet (complete task action)
        Increases health and gives more XP
        """
        self.health = min(100, self.health + 15)
        self.last_played = func.now()
        return self.add_xp(xp_amount)
    
    def decay_stats(self, hours_passed: int) -> dict:
        """
        Decay happiness and health based on inactivity
        Called by scheduled task
        """
        # Decrease 5 points per day (24 hours)
        happiness_loss = int((hours_passed / 24) * 5)
        health_loss = int((hours_passed / 24) * 5)
        
        self.happiness = max(0, self.happiness - happiness_loss)
        self.health = max(0, self.health - health_loss)
        
        return {
            "happiness": self.happiness,
            "health": self.health,
            "needs_attention": self.happiness < 30 or self.health < 30,
        }
    
    def get_emotion(self, time_of_day: str = "day", user_streak: int = 0) -> str:
        """
        Get current pet emotion based on stats and context
        
        Emotions: happy, sad, sleepy, excited, loving, celebrating, thinking, cool
        """
        # Priority emotions (override everything)
        if user_streak >= 7:
            return "celebrating"  # 🥳
        
        if self.happiness < 20 or self.health < 20:
            return "sad"  # 😢
        
        # Time-based emotions
        if time_of_day == "night":
            return "sleepy"  # 😴
        
        # Stat-based emotions
        if self.happiness >= 90 and self.health >= 90:
            return "excited"  # 🤩
        
        if self.happiness >= 70:
            return "happy"  # 😊
        
        if self.level >= 30:
            return "cool"  # 😎
        
        return "thinking"  # 🤔
    
    def get_speech_bubble(self, emotion: str = None) -> str:
        """Get random speech bubble text based on emotion"""
        import random
        
        if not emotion:
            emotion = self.get_emotion()
        
        messages = {
            "happy": [
                "Я счастлив сегодня! 😊",
                "Отличный день!",
                "Давай создадим воспоминание?",
                "Спасибо что заботишься обо мне!",
                "Я очень рад тебя видеть!",
            ],
            "sad": [
                "Мне грустно... 😢",
                "Я соскучился...",
                "Можем провести время вместе?",
                "Мне нужна твоя забота...",
            ],
            "sleepy": [
                "Хочу спать... 😴",
                "Уже поздно...",
                "Спокойной ночи!",
                "Увидимся завтра!",
            ],
            "excited": [
                "Вау! Это потрясающе! 🤩",
                "Я на вершине мира!",
                "У нас получается!",
                "Продолжаем в том же духе!",
            ],
            "loving": [
                "Я тебя люблю! 😍",
                "Ты лучший!",
                "Спасибо за подарок!",
                "Ты особенный для меня!",
            ],
            "celebrating": [
                "Поздравляю с серией! 🥳",
                "Мы молодцы!",
                "Так держать!",
                "7 дней подряд - это круто!",
            ],
            "thinking": [
                "Хм... 🤔",
                "Интересно...",
                "Что будем делать?",
                "Есть идеи?",
            ],
            "cool": [
                "Я крут! 😎",
                "Уровень {level} - не шутки!",
                "Мы команда!",
                "Ничто нас не остановит!",
            ],
        }
        
        bubble_messages = messages.get(emotion, messages["thinking"])
        message = random.choice(bubble_messages)
        
        # Replace placeholders
        message = message.replace("{level}", str(self.level))
        message = message.replace("{name}", self.name)
        
        return message

