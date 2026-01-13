"""Email verification code service using Redis"""
import random
import redis.asyncio as redis
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Service for generating and verifying email codes"""
    
    # Redis connection
    _redis: Optional[redis.Redis] = None
    
    # Code settings
    CODE_LENGTH = 6
    CODE_TTL = 300  # 5 minutes
    MAX_ATTEMPTS = 3
    
    @classmethod
    async def _get_redis(cls) -> redis.Redis:
        """Get or create Redis connection"""
        if cls._redis is None:
            cls._redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._redis
    
    @classmethod
    def _generate_code(cls) -> str:
        """Generate random 6-digit code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(cls.CODE_LENGTH)])
    
    @classmethod
    def _get_redis_key(cls, email: str) -> str:
        """Get Redis key for email"""
        return f"email_code:{email.lower()}"
    
    @classmethod
    def _get_attempts_key(cls, email: str) -> str:
        """Get Redis key for attempts counter"""
        return f"email_attempts:{email.lower()}"
    
    @classmethod
    async def generate_and_store_code(cls, email: str) -> str:
        """
        Generate new verification code and store in Redis
        
        Args:
            email: Email address
            
        Returns:
            Generated code
        """
        code = cls._generate_code()
        r = await cls._get_redis()
        
        # Store code with TTL
        key = cls._get_redis_key(email)
        await r.setex(key, cls.CODE_TTL, code)
        
        # Reset attempts counter
        attempts_key = cls._get_attempts_key(email)
        await r.delete(attempts_key)
        
        logger.info(f"🔑 [EMAIL_VERIFY] Generated code for {email} (TTL: {cls.CODE_TTL}s)")
        
        return code
    
    @classmethod
    async def verify_code(cls, email: str, code: str) -> bool:
        """
        Verify email code
        
        Args:
            email: Email address
            code: Code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        r = await cls._get_redis()
        
        # Check attempts
        attempts_key = cls._get_attempts_key(email)
        attempts = await r.get(attempts_key)
        attempts = int(attempts) if attempts else 0
        
        if attempts >= cls.MAX_ATTEMPTS:
            logger.warning(f"⚠️ [EMAIL_VERIFY] Max attempts reached for {email}")
            return False
        
        # Get stored code
        key = cls._get_redis_key(email)
        stored_code = await r.get(key)
        
        if not stored_code:
            logger.warning(f"⚠️ [EMAIL_VERIFY] No code found for {email} (expired or not sent)")
            return False
        
        # Verify code
        if code == stored_code:
            logger.info(f"✅ [EMAIL_VERIFY] Code verified for {email}")
            
            # Delete code after successful verification
            await r.delete(key)
            await r.delete(attempts_key)
            
            return True
        else:
            # Increment attempts
            await r.incr(attempts_key)
            await r.expire(attempts_key, cls.CODE_TTL)
            
            logger.warning(f"❌ [EMAIL_VERIFY] Invalid code for {email} (attempt {attempts + 1}/{cls.MAX_ATTEMPTS})")
            
            return False
    
    @classmethod
    async def get_remaining_attempts(cls, email: str) -> int:
        """Get remaining verification attempts"""
        r = await cls._get_redis()
        attempts_key = cls._get_attempts_key(email)
        attempts = await r.get(attempts_key)
        attempts = int(attempts) if attempts else 0
        
        return max(0, cls.MAX_ATTEMPTS - attempts)
    
    @classmethod
    async def is_code_expired(cls, email: str) -> bool:
        """Check if code exists for email"""
        r = await cls._get_redis()
        key = cls._get_redis_key(email)
        exists = await r.exists(key)
        return exists == 0
    
    @classmethod
    async def get_code_ttl(cls, email: str) -> Optional[int]:
        """Get remaining TTL for code in seconds"""
        r = await cls._get_redis()
        key = cls._get_redis_key(email)
        ttl = await r.ttl(key)
        
        return ttl if ttl > 0 else None
