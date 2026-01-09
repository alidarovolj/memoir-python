"""Pet mini-games models"""
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class GameType(str, enum.Enum):
    """Available mini-games"""
    FEED_FRENZY = "feed_frenzy"
    HIDE_AND_SEEK = "hide_and_seek"
    MEMORY_MATCH = "memory_match"


class PetGameSession(Base):
    """
    Pet game session - track game plays
    """
    __tablename__ = "pet_game_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False)
    
    # Game info
    game_type = Column(SQLEnum(GameType), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    xp_earned = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    played_at = Column(String(100), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    pet = relationship("Pet")
    
    def __repr__(self):
        return f"<PetGameSession {self.game_type} score={self.score}>"


class PetGameStats(Base):
    """
    Aggregate game statistics per user
    """
    __tablename__ = "pet_game_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Total stats
    total_games_played = Column(Integer, default=0, nullable=False)
    total_xp_earned = Column(Integer, default=0, nullable=False)
    
    # Per-game stats
    feed_frenzy_plays = Column(Integer, default=0, nullable=False)
    feed_frenzy_high_score = Column(Integer, default=0, nullable=False)
    
    hide_and_seek_plays = Column(Integer, default=0, nullable=False)
    hide_and_seek_high_score = Column(Integer, default=0, nullable=False)
    
    memory_match_plays = Column(Integer, default=0, nullable=False)
    memory_match_high_score = Column(Integer, default=0, nullable=False)
    
    # Daily limit tracking
    games_played_today = Column(Integer, default=0, nullable=False)
    last_played_date = Column(String(50))  # YYYY-MM-DD
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<PetGameStats user={self.user_id} total={self.total_games_played}>"
