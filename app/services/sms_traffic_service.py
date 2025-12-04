"""SMS Traffic service for sending SMS codes"""
import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSTrafficService:
    """Service for SMS Traffic API integration"""
    
    BASE_URL = "https://multi.smstraffic.ru/multi.php"
    
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
            logger.info(f"📱 [SMS_TRAFFIC] Sending SMS to {phone}")
            
            params = {
                "login": settings.SMS_TRAFFIC_LOGIN,
                "password": settings.SMS_TRAFFIC_PASSWORD,
                "phones": phone,
                "message": message,
                "originator": originator,
                "rus": "5",  # Translit=5 for Russian text
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(cls.BASE_URL, params=params)
                response_text = response.text.strip()
                
                logger.info(f"📡 [SMS_TRAFFIC] Response: {response_text}")
                
                # Parse response
                # Format: <result><code>OK</code><description>...</description></result>
                # or <result><code>ERROR</code><description>...</description></result>
                
                if "<code>OK</code>" in response_text:
                    # Extract SMS ID
                    sms_id = None
                    if "<sms_id>" in response_text:
                        start = response_text.find("<sms_id>") + 8
                        end = response_text.find("</sms_id>")
                        sms_id = response_text[start:end]
                    
                    logger.info(f"✅ [SMS_TRAFFIC] SMS sent successfully. ID: {sms_id}")
                    
                    return {
                        "success": True,
                        "sms_id": sms_id,
                        "message": "SMS sent successfully"
                    }
                else:
                    # Extract error description
                    error_msg = "Unknown error"
                    if "<description>" in response_text:
                        start = response_text.find("<description>") + 13
                        end = response_text.find("</description>")
                        error_msg = response_text[start:end]
                    
                    logger.error(f"❌ [SMS_TRAFFIC] Failed to send SMS: {error_msg}")
                    
                    return {
                        "success": False,
                        "error": error_msg
                    }
                    
        except httpx.TimeoutException:
            logger.error("❌ [SMS_TRAFFIC] Request timeout")
            return {
                "success": False,
                "error": "SMS service timeout"
            }
        except Exception as e:
            logger.error(f"❌ [SMS_TRAFFIC] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    async def check_balance(cls) -> Optional[float]:
        """
        Check SMS Traffic account balance
        
        Returns:
            Balance amount or None if error
        """
        try:
            params = {
                "login": settings.SMS_TRAFFIC_LOGIN,
                "password": settings.SMS_TRAFFIC_PASSWORD,
                "operation": "balance",
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.BASE_URL, params=params)
                response_text = response.text.strip()
                
                # Format: <balance>1234.56</balance>
                if "<balance>" in response_text:
                    start = response_text.find("<balance>") + 9
                    end = response_text.find("</balance>")
                    balance = float(response_text[start:end])
                    
                    logger.info(f"💰 [SMS_TRAFFIC] Balance: {balance}")
                    return balance
                else:
                    logger.error(f"❌ [SMS_TRAFFIC] Failed to get balance: {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ [SMS_TRAFFIC] Balance check error: {e}")
            return None

