"""Authentication service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""
    
    # NOTE: Firebase Phone Auth был заменён на SMS Traffic
    # Firebase остаётся только для Push Notifications (FCM)
    # Метод register_or_login_with_phone больше не используется
    
    @staticmethod
    def generate_tokens(user_id: str) -> dict:
        """Generate access and refresh tokens"""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

