"""Token Pydantic schemas"""
from pydantic import BaseModel
from app.schemas.user import User


class Token(BaseModel):
    """Access token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    """Token with user response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User


class TokenPayload(BaseModel):
    """Token payload"""
    sub: str | None = None
    exp: int | None = None
    type: str = "access"


class LoginRequest(BaseModel):
    """Login request"""
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str
