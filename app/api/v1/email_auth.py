"""Email-based authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr
import logging

from app.db.session import get_db
from app.schemas.user import User
from app.schemas.token import TokenWithUser
from app.services.email_service import EmailService
from app.services.email_verification_service import EmailVerificationService
from app.services.auth_service import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


class SendEmailCodeRequest(BaseModel):
    """Request to send email verification code"""
    email: EmailStr


class VerifyEmailCodeRequest(BaseModel):
    """Request to verify email code"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/send-code", status_code=status.HTTP_200_OK)
async def send_email_verification_code(
    request: SendEmailCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send email verification code
    
    Generates a 6-digit code, stores it in Redis (TTL 5 min), 
    and sends via email
    """
    try:
        email = request.email.lower().strip()
        logger.info(f"📧 [EMAIL_AUTH] Send code request for: {email}")
        
        # Generate and store code
        code = await EmailVerificationService.generate_and_store_code(email)
        
        # Send email
        result = await EmailService.send_verification_code(email, code)
        
        if not result.get("success"):
            logger.error(f"❌ [EMAIL_AUTH] Failed to send email: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {result.get('error')}"
            )
        
        logger.info(f"✅ [EMAIL_AUTH] Code sent successfully to {email}")
        
        return {
            "success": True,
            "message": "Verification code sent to email",
            "expires_in": EmailVerificationService.CODE_TTL
        }
        
    except Exception as e:
        logger.error(f"❌ [EMAIL_AUTH] Error sending code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )


@router.post("/verify-code", response_model=TokenWithUser, status_code=status.HTTP_200_OK)
async def verify_email_code_and_login(
    request: VerifyEmailCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email code and authenticate user
    
    If code is valid:
    - Register new user if doesn't exist
    - Login existing user
    - Return JWT token + user data
    """
    try:
        email = request.email.lower().strip()
        code = request.code.strip()
        
        logger.info(f"🔍 [EMAIL_AUTH] Verify code for: {email}")
        
        # Check remaining attempts
        remaining = await EmailVerificationService.get_remaining_attempts(email)
        if remaining == 0:
            logger.warning(f"⚠️ [EMAIL_AUTH] Max attempts reached for {email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum verification attempts reached. Request new code."
            )
        
        # Verify code
        is_valid = await EmailVerificationService.verify_code(email, code)
        
        if not is_valid:
            remaining_after = await EmailVerificationService.get_remaining_attempts(email)
            logger.warning(f"❌ [EMAIL_AUTH] Invalid code for {email}. Remaining attempts: {remaining_after}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid verification code. {remaining_after} attempts remaining."
            )
        
        # Code is valid - authenticate or register user
        logger.info(f"✅ [EMAIL_AUTH] Code verified for {email}. Authenticating...")
        
        from app.models.user import User as UserModel
        from sqlalchemy import select
        
        # Check if user exists
        result = await db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"🔑 [EMAIL_AUTH] Existing user login: {email}")
        else:
            # Create new user
            username = email.split('@')[0]
            
            # Check if username exists
            base_username = username
            counter = 1
            while True:
                result = await db.execute(select(UserModel).where(UserModel.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{base_username}{counter}"
                counter += 1
            
            # Generate phone number placeholder (can be updated later)
            import time
            phone_placeholder = f"+email_{int(time.time())}"
            
            user = UserModel(
                email=email,
                username=username,
                phone_number=phone_placeholder,  # Required field, will be updated if user adds phone
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"✨ [EMAIL_AUTH] New user registered: {email}")
        
        # Generate tokens
        tokens = AuthService.generate_tokens(str(user.id))
        
        return {
            **tokens,
            "user": user,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [EMAIL_AUTH] Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/resend-code", status_code=status.HTTP_200_OK)
async def resend_email_verification_code(
    request: SendEmailCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend email verification code
    
    Same as send-code, but with logging for resend
    """
    logger.info(f"🔄 [EMAIL_AUTH] Resend code request for: {request.email}")
    return await send_email_verification_code(request, db)
