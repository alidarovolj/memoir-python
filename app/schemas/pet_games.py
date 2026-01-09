"""Pet games schemas"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class GameType(str, Enum):
    """Available mini-games"""
    FEED_FRENZY = "feed_frenzy"
    HIDE_AND_SEEK = "hide_and_seek"
    MEMORY_MATCH = "memory_match"


class PlayGameRequest(BaseModel):
    """Request to start a game"""
    game_type: GameType = Field(..., alias="gameType")
    
    class Config:
        use_enum_values = True
        populate_by_name = True


class CompleteGameRequest(BaseModel):
    """Request to complete a game with score"""
    game_type: GameType = Field(..., alias="gameType")
    score: int
    
    class Config:
        use_enum_values = True
        populate_by_name = True


class GameSessionResponse(BaseModel):
    """Game session result"""
    id: str
    game_type: GameType = Field(..., alias="gameType")
    score: int
    xp_earned: int = Field(..., alias="xpEarned")
    played_at: str = Field(..., alias="playedAt")
    is_high_score: bool = Field(default=False, alias="isHighScore")
    
    class Config:
        use_enum_values = True
        populate_by_name = True
        by_alias = True


class GameStatsResponse(BaseModel):
    """User's game statistics"""
    total_games_played: int = Field(..., alias="totalGamesPlayed")
    total_xp_earned: int = Field(..., alias="totalXpEarned")
    games_played_today: int = Field(..., alias="gamesPlayedToday")
    daily_limit: int = Field(default=3, alias="dailyLimit")
    can_play: bool = Field(..., alias="canPlay")
    
    # Per-game stats
    feed_frenzy: dict = Field(..., alias="feedFrenzy")
    hide_and_seek: dict = Field(..., alias="hideAndSeek")
    memory_match: dict = Field(..., alias="memoryMatch")
    
    class Config:
        populate_by_name = True
        by_alias = True
