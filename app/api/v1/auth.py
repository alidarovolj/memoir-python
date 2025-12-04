"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserCreate, User
from app.schemas.token import Token, TokenWithUser, LoginRequest, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError

router = APIRouter()


@router.post("/register", response_model=TokenWithUser, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register new user"""
    try:
        user = await AuthService.register_user(db, user_data)
        tokens = AuthService.generate_tokens(str(user.id))
        
        return {
            **tokens,
            "user": user,
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login user"""
    user = await AuthService.authenticate_user(
        db, 
        login_data.email, 
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    tokens = AuthService.generate_tokens(str(user.id))
    return tokens


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
