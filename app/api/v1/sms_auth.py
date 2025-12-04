"""SMS-based authentication endpoints using Mobizon"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging

from app.db.session import get_db
from app.schemas.user import User
from app.schemas.token import TokenWithUser
from app.services.mobizon_service import MobizonService
from app.services.sms_verification_service import SMSVerificationService
from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError

router = APIRouter()
logger = logging.getLogger(__name__)


class SendCodeRequest(BaseModel):
    """Request to send SMS code"""
    phone_number: str = Field(..., min_length=10, max_length=20)


class VerifyCodeRequest(BaseModel):
    """Request to verify SMS code"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/send-code", status_code=status.HTTP_200_OK)
async def send_verification_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send SMS verification code
    
    Generates a 6-digit code, stores it in Redis (TTL 5 min), 
    and sends via SMS Traffic
    """
    try:
        phone = request.phone_number.strip()
        logger.info(f"📱 [SMS_AUTH] Send code request for: {phone}")
        
        # Generate and store code
        code = await SMSVerificationService.generate_and_store_code(phone)
        
        # Send SMS via Mobizon
        message = f"Ваш код подтверждения Memoir: {code}\n\nКод действителен 5 минут."
        
        result = await MobizonService.send_sms(
            phone=phone,
            message=message,
            originator="Memoir"
        )
        
        if not result.get("success"):
            logger.error(f"❌ [SMS_AUTH] Failed to send SMS: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send SMS: {result.get('error')}"
            )
        
        logger.info(f"✅ [SMS_AUTH] Code sent successfully to {phone}")
        
        return {
            "success": True,
            "message": "Verification code sent",
            "sms_id": result.get("sms_id"),
            "expires_in": SMSVerificationService.CODE_TTL
        }
        
    except Exception as e:
        logger.error(f"❌ [SMS_AUTH] Error sending code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )


@router.post("/verify-code", response_model=TokenWithUser, status_code=status.HTTP_200_OK)
async def verify_code_and_login(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify SMS code and authenticate user
    
    If code is valid:
    - Register new user if doesn't exist
    - Login existing user
    - Return JWT token + user data
    """
    try:
        phone = request.phone_number.strip()
        code = request.code.strip()
        
        logger.info(f"🔍 [SMS_AUTH] Verify code for: {phone}")
        
        # Check remaining attempts
        remaining = await SMSVerificationService.get_remaining_attempts(phone)
        if remaining == 0:
            logger.warning(f"⚠️ [SMS_AUTH] Max attempts reached for {phone}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum verification attempts reached. Request new code."
            )
        
        # Verify code
        is_valid = await SMSVerificationService.verify_code(phone, code)
        
        if not is_valid:
            remaining_after = await SMSVerificationService.get_remaining_attempts(phone)
            logger.warning(f"❌ [SMS_AUTH] Invalid code for {phone}. Remaining attempts: {remaining_after}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid verification code. {remaining_after} attempts remaining."
            )
        
        # Code is valid - authenticate or register user
        logger.info(f"✅ [SMS_AUTH] Code verified for {phone}. Authenticating...")
        
        # Use existing auth service to create/get user
        from app.models.user import User as UserModel
        from sqlalchemy import select
        
        # Check if user exists
        result = await db.execute(select(UserModel).where(UserModel.phone_number == phone))
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"🔑 [SMS_AUTH] Existing user login: {phone}")
        else:
            # Create new user
            username = f"user_{phone[-4:]}"
            
            # Check if username exists
            base_username = username
            counter = 1
            while True:
                result = await db.execute(select(UserModel).where(UserModel.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{base_username}{counter}"
                counter += 1
            
            user = UserModel(
                phone_number=phone,
                username=username,
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"✨ [SMS_AUTH] New user registered: {phone}")
        
        # Generate tokens
        tokens = AuthService.generate_tokens(str(user.id))
        
        return {
            **tokens,
            "user": user,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SMS_AUTH] Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/resend-code", status_code=status.HTTP_200_OK)
async def resend_verification_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend SMS verification code
    
    Same as send-code, but with logging for resend
    """
    logger.info(f"🔄 [SMS_AUTH] Resend code request for: {request.phone_number}")
    return await send_verification_code(request, db)

