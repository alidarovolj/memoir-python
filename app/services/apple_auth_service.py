"""Apple OAuth authentication service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import jwt
import logging
import httpx
from typing import Optional

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AppleAuthService:
    """Service for Apple OAuth authentication"""

    @staticmethod
    async def authenticate_with_apple(
        db: AsyncSession,
        identity_token: str,
        authorization_code: Optional[str] = None,
        user_identifier: Optional[str] = None,
        email: Optional[str] = None,
        given_name: Optional[str] = None,
        family_name: Optional[str] = None,
    ) -> dict:
        """
        Authenticate user with Apple ID token
        
        Args:
            db: Database session
            identity_token: Apple identity token from client
            authorization_code: Apple authorization code
            user_identifier: Apple user identifier
            email: User email (only provided on first sign in)
            given_name: User first name (only provided on first sign in)
            family_name: User last name (only provided on first sign in)
            
        Returns:
            dict with user info, tokens, and is_new_user flag
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Декодируем токен БЕЗ верификации (для быстрого старта)
            # TODO: Добавить верификацию через Apple public keys для production
            decoded = jwt.decode(
                identity_token,
                options={"verify_signature": False}
            )

            apple_id = decoded.get('sub')
            token_email = decoded.get('email')
            email_verified = decoded.get('email_verified', 'false') == 'true'
            
            # Используем email из токена или из параметров
            final_email = email or token_email
            
            if not apple_id:
                raise ValueError("Invalid Apple token: missing user identifier")

            logger.info(f"Apple auth for user: {apple_id}, email: {final_email}")

            # Проверяем существование пользователя по apple_id или email
            conditions = [User.apple_id == apple_id]
            if final_email:
                conditions.append(User.email == final_email)
            
            query = select(User).where(or_(*conditions))
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            is_new_user = False

            if user:
                # Обновляем существующего пользователя
                if not user.apple_id:
                    user.apple_id = apple_id
                if not user.email and final_email:
                    user.email = final_email
                    
                await db.commit()
                await db.refresh(user)
                logger.info(f"Existing user logged in: {user.id}")
            else:
                # Создаем нового пользователя
                # Генерируем username из email или apple_id
                username = final_email.split('@')[0] if final_email else f"apple_{apple_id[:8]}"
                
                user = User(
                    email=final_email,
                    apple_id=apple_id,
                    first_name=given_name,
                    last_name=family_name,
                    username=username,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                is_new_user = True
                logger.info(f"New user created: {user.id}")

            # Генерируем JWT токены
            tokens = AuthService.generate_tokens(str(user.id))

            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "is_new_user": is_new_user,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "avatar_url": user.avatar_url,
                }
            }

        except jwt.DecodeError as e:
            logger.error(f"Apple token decode failed: {str(e)}")
            raise ValueError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            logger.error(f"Apple auth failed: {str(e)}")
            raise
