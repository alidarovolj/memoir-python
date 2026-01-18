"""Google OAuth authentication service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Google OAuth Client ID из Firebase
GOOGLE_CLIENT_ID = "660553470030-as8ms2ovb1cb3tk2ii50s1a4iaq1ea0d.apps.googleusercontent.com"


class GoogleAuthService:
    """Service for Google OAuth authentication"""

    @staticmethod
    async def authenticate_with_google(
        db: AsyncSession,
        id_token_str: str,
    ) -> dict:
        """
        Authenticate user with Google ID token
        
        Args:
            db: Database session
            id_token_str: Google ID token from client
            
        Returns:
            dict with user info, tokens, and is_new_user flag
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify the Google ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )

            # Extract user info from token
            google_id = idinfo['sub']
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)
            
            if not email or not email_verified:
                raise ValueError("Email not verified")

            name = idinfo.get('name', '')
            given_name = idinfo.get('given_name')
            family_name = idinfo.get('family_name')
            picture = idinfo.get('picture')

            logger.info(f"Google auth for email: {email}")

            # Check if user exists by email or google_id
            result = await db.execute(
                select(User).where(
                    (User.email == email) | (User.google_id == google_id)
                )
            )
            user = result.scalar_one_or_none()

            is_new_user = False

            if user:
                # Update existing user with Google info
                if not user.google_id:
                    user.google_id = google_id
                if not user.email:
                    user.email = email
                if not user.avatar_url and picture:
                    user.avatar_url = picture
                    
                await db.commit()
                await db.refresh(user)
                logger.info(f"Existing user logged in: {user.id}")
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    first_name=given_name or name.split()[0] if name else None,
                    last_name=family_name or (name.split()[1] if len(name.split()) > 1 else None),
                    avatar_url=picture,
                    username=email.split('@')[0],  # Generate username from email
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                is_new_user = True
                logger.info(f"New user created: {user.id}")

            # Generate tokens
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

        except ValueError as e:
            logger.error(f"Google token verification failed: {str(e)}")
            raise ValueError(f"Invalid Google token: {str(e)}")
        except Exception as e:
            logger.error(f"Google auth failed: {str(e)}")
            raise
