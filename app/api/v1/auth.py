"""Authentication endpoints (legacy - Firebase auth deprecated)"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user import User
from app.schemas.token import Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.security import decode_token

router = APIRouter()
logger = logging.getLogger(__name__)


# NOTE: Phone authentication moved to /sms-auth endpoints
# This file kept for backward compatibility (refresh token, /me endpoint)


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
