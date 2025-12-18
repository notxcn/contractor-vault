"""
Contractor Vault - Discord Webhook Service
Sends notifications to Discord for key events
"""
import logging
import httpx
from typing import Optional
from app.config import get_settings

logger = logging.getLogger("contractor_vault.discord")


class DiscordWebhookService:
    """Service for sending notifications to Discord via webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        settings = get_settings()
        self.webhook_url = webhook_url or getattr(settings, 'discord_webhook_url', None)
        self.enabled = bool(self.webhook_url)
        
        if self.enabled:
            logger.info("Discord webhook notifications enabled")
        else:
            logger.debug("Discord webhook not configured - notifications disabled")
    
    async def send_message(
        self,
        content: str,
        username: str = "Contractor Vault",
        avatar_url: str = "https://cdn.discordapp.com/embed/avatars/0.png",
    ) -> bool:
        """
        Send a simple text message to Discord.
        
        Args:
            content: The message text (max 2000 chars)
            username: Bot username to display
            avatar_url: Bot avatar URL
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "content": content,
                        "username": username,
                        "avatar_url": avatar_url,
                    },
                    timeout=10.0,
                )
                
                if response.status_code in (200, 204):
                    logger.debug(f"Discord notification sent: {content[:50]}...")
                    return True
                else:
                    logger.warning(f"Discord webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    async def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x5865F2,  # Discord blurple
        fields: Optional[list[dict]] = None,
        footer: Optional[str] = None,
    ) -> bool:
        """
        Send a rich embed message to Discord.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: List of {name, value, inline} dicts
            footer: Footer text
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
            
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": None,
        }
        
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = {"text": footer}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "username": "🔐 Contractor Vault",
                        "embeds": [embed],
                    },
                    timeout=10.0,
                )
                
                if response.status_code in (200, 204):
                    logger.debug(f"Discord embed sent: {title}")
                    return True
                else:
                    logger.warning(f"Discord webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    # Pre-built notification methods for common events
    
    async def notify_access_granted(
        self,
        contractor_email: str,
        credential_name: str,
        duration_minutes: int,
        admin_email: str,
    ):
        """Notify when access is granted to a contractor."""
        await self.send_embed(
            title="🎫 Access Granted",
            description=f"New temporary access created",
            color=0x57F287,  # Green
            fields=[
                {"name": "Contractor", "value": contractor_email, "inline": True},
                {"name": "Credential", "value": credential_name, "inline": True},
                {"name": "Duration", "value": f"{duration_minutes} minutes", "inline": True},
                {"name": "Granted By", "value": admin_email, "inline": True},
            ],
        )
    
    async def notify_access_claimed(
        self,
        contractor_email: str,
        credential_name: str,
        ip_address: str,
    ):
        """Notify when a contractor claims their access."""
        await self.send_embed(
            title="✅ Access Claimed",
            description=f"Contractor claimed their credentials",
            color=0x5865F2,  # Blurple
            fields=[
                {"name": "Contractor", "value": contractor_email, "inline": True},
                {"name": "Credential", "value": credential_name, "inline": True},
                {"name": "IP Address", "value": ip_address, "inline": True},
            ],
        )
    
    async def notify_access_revoked(
        self,
        contractor_email: str,
        credential_name: str,
        admin_email: str,
        reason: Optional[str] = None,
    ):
        """Notify when access is revoked."""
        fields = [
            {"name": "Contractor", "value": contractor_email, "inline": True},
            {"name": "Credential", "value": credential_name, "inline": True},
            {"name": "Revoked By", "value": admin_email, "inline": True},
        ]
        if reason:
            fields.append({"name": "Reason", "value": reason, "inline": False})
            
        await self.send_embed(
            title="🚫 Access Revoked",
            description=f"Contractor access terminated",
            color=0xED4245,  # Red
            fields=fields,
        )
    
    async def notify_kill_switch(
        self,
        contractor_email: str,
        revoked_count: int,
        admin_email: str,
        reason: Optional[str] = None,
    ):
        """Notify when kill switch is activated."""
        fields = [
            {"name": "Contractor", "value": contractor_email, "inline": True},
            {"name": "Tokens Revoked", "value": str(revoked_count), "inline": True},
            {"name": "Revoked By", "value": admin_email, "inline": True},
        ]
        if reason:
            fields.append({"name": "Reason", "value": reason, "inline": False})
            
        await self.send_embed(
            title="⚠️ KILL SWITCH ACTIVATED",
            description=f"All access for contractor terminated immediately",
            color=0xED4245,  # Red
            fields=fields,
        )


    async def notify_shadow_it_detection(
        self,
        contractor_email: str,
        service_name: str,
        detection_type: str,
        subject: str,
    ):
        """Notify when Shadow IT is detected."""
        await self.send_embed(
            title="🕵️ Shadow IT Detected",
            description=f"Contractor signed up for a new service",
            color=0xFEE75C,  # Yellow
            fields=[
                {"name": "Contractor", "value": contractor_email, "inline": True},
                {"name": "Service", "value": service_name, "inline": True},
                {"name": "Detection Type", "value": detection_type, "inline": True},
                {"name": "Subject/Context", "value": subject, "inline": False},
            ],
            footer="Review in dashboard",
        )

    async def notify_security_alert(
        self,
        alert_type: str,
        details: str,
    ):
        """Notify when a security alert occurs."""
        await self.send_embed(
            title="🚨 Security Alert",
            description=f"Security violation detected",
            color=0xED4245,  # Red
            fields=[
                {"name": "Alert Type", "value": alert_type, "inline": True},
                {"name": "Details", "value": details, "inline": False},
            ],
            footer="Immediate investigation recommended",
        )


# Singleton instance
_discord_service: Optional[DiscordWebhookService] = None


def get_discord_service() -> DiscordWebhookService:
    """Get the Discord webhook service singleton."""
    global _discord_service
    if _discord_service is None:
        _discord_service = DiscordWebhookService()
    return _discord_service
