"""Mobizon service for sending SMS codes"""
import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class MobizonService:
    """Service for Mobizon API integration (Kazakhstan)"""
    
    BASE_URL = "https://api.mobizon.kz/service"
    
    @classmethod
    async def send_sms(
        cls,
        phone: str,
        message: str,
        originator: str = "Memoir"
    ) -> dict:
        """
        Send SMS via SMS Traffic API
        
        Args:
            phone: Phone number in international format (without +)
            message: SMS text
            originator: Sender name (max 11 chars for alphanumeric)
            
        Returns:
            Response dict with status
        """
        try:
            logger.info(f"📱 [MOBIZON] Sending SMS to {phone}")
            
            # TEST MODE: Just log the code instead of sending SMS
            if settings.SMS_TEST_MODE:
                logger.warning(f"🧪 [MOBIZON] TEST MODE - SMS not sent")
                logger.warning(f"📝 [MOBIZON] Message: {message}")
                return {
                    "success": True,
                    "sms_id": "test-mode-id",
                    "message": "SMS sent (test mode)"
                }
            
            # Mobizon API endpoint: https://api.mobizon.kz/service/message/sendsmsmessage
            endpoint = f"{cls.BASE_URL}/message/sendsmsmessage"
            
            # Clean phone number (remove + if present)
            clean_phone = phone.replace('+', '')
            
            # Mobizon API parameters - все в query string
            # Согласно документации: https://mobizon.kz/help/api-docs/message
            params = {
                "apiKey": settings.MOBIZON_API_KEY,
                "recipient": clean_phone,
                "text": message,
                "output": "json",  # Explicitly request JSON response
            }
            
            # Добавляем подпись отправителя если указана
            if originator:
                params["from"] = originator
            
            logger.info(f"📡 [MOBIZON] Request URL: {endpoint}")
            logger.info(f"📡 [MOBIZON] Params: {params}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                logger.info(f"📡 [MOBIZON] HTTP Status: {response.status_code}")
                response_data = response.json()
                logger.info(f"📡 [MOBIZON] Response: {response_data}")
                
                # Mobizon response format:
                # {
                #   "code": 0,  // 0 = success, other = error
                #   "data": {...},
                #   "message": "..."
                # }
                
                if response_data.get("code") == 0:
                    message_id = response_data.get("data", {}).get("messageId")
                    
                    logger.info(f"✅ [MOBIZON] SMS sent successfully. ID: {message_id}")
                    
                    return {
                        "success": True,
                        "sms_id": message_id,
                        "message": "SMS sent successfully"
                    }
                else:
                    error_msg = response_data.get("message", "Unknown error")
                    error_code = response_data.get("code")
                    
                    logger.error(f"❌ [MOBIZON] Failed to send SMS (code {error_code}): {error_msg}")
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": error_code
                    }
                    
        except httpx.TimeoutException:
            logger.error("❌ [MOBIZON] Request timeout")
            return {
                "success": False,
                "error": "SMS service timeout"
            }
        except Exception as e:
            logger.error(f"❌ [MOBIZON] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    async def check_balance(cls) -> Optional[float]:
        """
        Check Mobizon account balance
        Документация: https://mobizon.kz/help/api-docs/sms-api
        
        Returns:
            Balance amount or None if error
        """
        try:
            endpoint = f"{cls.BASE_URL}/user/getownbalance"
            
            params = {
                "apiKey": settings.MOBIZON_API_KEY,
                "output": "json",
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint, params=params)
                response_data = response.json()
                
                if response_data.get("code") == 0:
                    balance = response_data.get("data", {}).get("balance")
                    currency = response_data.get("data", {}).get("currency", "KZT")
                    
                    logger.info(f"💰 [MOBIZON] Balance: {balance} {currency}")
                    return float(balance) if balance else None
                else:
                    logger.error(f"❌ [MOBIZON] Failed to get balance: {response_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ [MOBIZON] Balance check error: {e}")
            return None

