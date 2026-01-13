"""Email service for sending verification codes and notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    @classmethod
    async def send_verification_code(cls, email: str, code: str) -> dict:
        """
        Send verification code via email
        
        Args:
            email: Recipient email address
            code: Verification code
            
        Returns:
            Response dict with status
        """
        try:
            logger.info(f"📧 [EMAIL] Sending verification code to {email}")
            
            # TEST MODE: Just log the code instead of sending email
            if settings.EMAIL_TEST_MODE:
                logger.warning(f"🧪 [EMAIL] TEST MODE - Email not sent")
                logger.warning(f"📝 [EMAIL] Code: {code} for {email}")
                return {
                    "success": True,
                    "message_id": "test-mode-id",
                    "message": "Email sent (test mode)"
                }
            
            # Create email message
            subject = "Код подтверждения Memoir"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #6366f1; text-align: center; margin-bottom: 20px;">Memoir</h1>
                        <h2 style="color: #333; text-align: center;">Код подтверждения</h2>
                        <p style="color: #666; font-size: 16px; line-height: 1.6;">
                            Используйте этот код для входа в приложение:
                        </p>
                        <div style="background-color: #f8f9ff; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                            <span style="font-size: 36px; font-weight: bold; color: #6366f1; letter-spacing: 8px;">{code}</span>
                        </div>
                        <p style="color: #999; font-size: 14px; text-align: center;">
                            Код действителен 5 минут
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Если вы не запрашивали этот код, просто проигнорируйте это письмо.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_body = f"""
            Memoir - Код подтверждения
            
            Используйте этот код для входа в приложение:
            
            {code}
            
            Код действителен 5 минут.
            
            Если вы не запрашивали этот код, просто проигнорируйте это письмо.
            """
            
            # Send email
            result = await cls._send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [EMAIL] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    async def _send_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> dict:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML version of email
            text_body: Plain text version of email
            
        Returns:
            Response dict with status
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            message["To"] = to_email
            
            # Add plain text and HTML versions
            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part1)
            message.attach(part2)
            
            # Connect to SMTP server and send
            logger.info(f"📡 [EMAIL] Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            
            if settings.SMTP_TLS:
                # Use TLS (port 587)
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                # Use SSL (port 465) or no encryption (port 25)
                if settings.SMTP_PORT == 465:
                    server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
                else:
                    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            
            # Login if credentials provided
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                logger.info(f"📡 [EMAIL] Authenticating as {settings.SMTP_USER}")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            # Send email
            server.send_message(message)
            server.quit()
            
            logger.info(f"✅ [EMAIL] Email sent successfully to {to_email}")
            
            return {
                "success": True,
                "message_id": "smtp-sent",
                "message": "Email sent successfully"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ [EMAIL] Authentication failed: {e}")
            return {
                "success": False,
                "error": "SMTP authentication failed. Check credentials."
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ [EMAIL] SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ [EMAIL] Error sending email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
