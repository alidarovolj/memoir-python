"""Authentication endpoints (legacy - Firebase auth deprecated)"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user import User
from app.schemas.token import Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.services.google_auth_service import GoogleAuthService
from app.services.apple_auth_service import AppleAuthService
from app.core.security import decode_token

router = APIRouter()
logger = logging.getLogger(__name__)


# NOTE: Phone authentication moved to /sms-auth endpoints
# This file kept for backward compatibility (refresh token, /me endpoint)


class GoogleAuthRequest(BaseModel):
    """Google authentication request"""
    id_token: str
    access_token: str | None = None


class AppleAuthRequest(BaseModel):
    """Apple authentication request"""
    identity_token: str
    authorization_code: Optional[str] = None
    user_identifier: Optional[str] = None
    email: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None


@router.post("/google", response_model=dict)
async def google_auth(
    auth_data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with Google"""
    try:
        result = await GoogleAuthService.authenticate_with_google(
            db=db,
            id_token_str=auth_data.id_token,
        )
        return result
    except ValueError as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Google auth unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate with Google",
        )


@router.post("/apple", response_model=dict)
async def apple_auth(
    auth_data: AppleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with Apple"""
    try:
        result = await AppleAuthService.authenticate_with_apple(
            db=db,
            identity_token=auth_data.identity_token,
            authorization_code=auth_data.authorization_code,
            user_identifier=auth_data.user_identifier,
            email=auth_data.email,
            given_name=auth_data.given_name,
            family_name=auth_data.family_name,
        )
        return result
    except ValueError as e:
        logger.error(f"Apple auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Apple auth unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate with Apple",
        )


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token"""
    payload = decode_token(refresh_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    tokens = AuthService.generate_tokens(user_id)
    return tokens


@router.get("/me", response_model=User)
async def get_me(
    current_user = Depends(get_current_user),
):
    """Get current user"""
    return current_user
