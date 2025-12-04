"""Application configuration using Pydantic Settings"""
from typing import List
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "Memoir"
    DEBUG: bool = False
    SECRET_KEY: str
    ENVIRONMENT: str = "production"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    
    # Redis
    REDIS_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_CLASSIFICATION: str = "gpt-4o-mini"
    OPENAI_MODEL_EMBEDDING: str = "text-embedding-3-small"
    
    # External APIs for Smart Search
    TMDB_API_KEY: str = ""  # The Movie Database
    GOOGLE_BOOKS_KEY: str = ""  # Google Books API
    GOOGLE_SEARCH_KEY: str = ""  # Google Custom Search API
    GOOGLE_SEARCH_CX: str = ""  # Custom Search Engine ID
    SPOONACULAR_KEY: str = ""  # Spoonacular API (recipes)
    
    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days (30 * 24 * 60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90  # 90 days
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [i.strip() for i in self.CORS_ORIGINS.split(",")]
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

