"""
Email service using Resend API for sending OTP codes
"""
import logging
import httpx
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend API."""
    
    RESEND_API_URL = "https://api.resend.com/emails"
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, 'resend_api_key', None)
        
    async def send_otp(self, to_email: str, otp_code: str) -> bool:
        """Send OTP code to user's email."""
        if not self.api_key:
            logger.error("Resend API key not configured")
            return False
            
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: #16213e; padding: 40px; border-radius: 12px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #00d9ff; margin-bottom: 20px; }}
                .code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #00d9ff; background: #0f3460; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                .footer {{ color: #888; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔐 Contractor Vault</div>
                <p>Your verification code is:</p>
                <div class="code">{otp_code}</div>
                <p>This code expires in 10 minutes.</p>
                <p>If you didn't request this code, you can safely ignore this email.</p>
                <div class="footer">
                    <p>Contractor Vault - Secure Session Management</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "from": "Contractor Vault <onboarding@resend.dev>",
            "to": [to_email],
            "subject": f"Your verification code: {otp_code}",
            "html": html_content
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.RESEND_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"OTP email sent to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send a generic email with custom subject and HTML content."""
        if not self.api_key:
            logger.error("Resend API key not configured")
            return False
        
        payload = {
            "from": "ShadowKey <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.RESEND_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Email sent to {to_email}: {subject}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False


def get_email_service() -> EmailService:
    """Get email service instance."""
    return EmailService()
