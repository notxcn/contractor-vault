"""
Contractor Vault - Device Service
Device fingerprinting, trust scoring, and validation
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from user_agents import parse as parse_user_agent

from app.models.device import DeviceInfo
from app.schemas.device import DeviceContext, DeviceValidationResult

logger = logging.getLogger(__name__)


class DeviceService:
    """
    Service for device trust management.
    
    Handles:
    - Device fingerprinting
    - Trust scoring
    - Anomaly detection
    - Device validation
    """
    
    # Trust score adjustments
    SCORE_NEW_DEVICE = 30
    SCORE_KNOWN_DEVICE = 50
    SCORE_TRUSTED_DEVICE = 90
    SCORE_PENALTY_FAILED_ATTEMPT = -10
    SCORE_BONUS_SUCCESSFUL_ACCESS = 2
    
    # Thresholds
    TRUST_THRESHOLD_LOW = 40
    TRUST_THRESHOLD_REQUIRE_PASSKEY = 50
    
    def compute_fingerprint(self, context: DeviceContext) -> str:
        """
        Compute a device fingerprint from context.
        
        Uses browser, OS, and other characteristics.
        """
        if context.fingerprint:
            return context.fingerprint
        
        # Fallback: compute from available data
        components = [
            context.user_agent or "",
            context.browser or "",
            context.os or "",
            context.device_type or "",
            context.screen_resolution or "",
            context.timezone or "",
            context.language or ""
        ]
        fingerprint_data = "|".join(components)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    def get_or_create_device(
        self,
        db: Session,
        contractor_email: str,
        context: DeviceContext,
        ip_address: Optional[str] = None
    ) -> Tuple[DeviceInfo, bool]:
        """
        Get existing device or create new one.
        
        Returns (device, is_new) tuple.
        """
        fingerprint = self.compute_fingerprint(context)
        
        # Look for existing device
        device = db.query(DeviceInfo).filter(
            DeviceInfo.fingerprint == fingerprint,
            DeviceInfo.contractor_email == contractor_email
        ).first()
        
        if device:
            # Update last seen
            device.last_seen = datetime.now(timezone.utc)
            device.access_count += 1
            if ip_address:
                device.ip_address = ip_address
            db.commit()
            return device, False
        
        # Parse user agent for details
        browser = context.browser
        browser_version = context.browser_version
        os = context.os
        os_version = context.os_version
        
        if context.user_agent and not browser:
            try:
                ua = parse_user_agent(context.user_agent)
                browser = ua.browser.family
                browser_version = ua.browser.version_string
                os = ua.os.family
                os_version = ua.os.version_string
            except Exception:
                pass
        
        # Create new device
        device = DeviceInfo(
            fingerprint=fingerprint,
            contractor_email=contractor_email,
            user_agent=context.user_agent,
            browser=browser,
            browser_version=browser_version,
            os=os,
            os_version=os_version,
            device_type=context.device_type,
            ip_address=ip_address,
            trust_score=self.SCORE_NEW_DEVICE
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        logger.info(f"New device registered for {contractor_email}: {fingerprint[:8]}...")
        return device, True
    
    def validate_device(
        self,
        db: Session,
        contractor_email: str,
        context: DeviceContext,
        ip_address: Optional[str] = None
    ) -> DeviceValidationResult:
        """
        Validate a device for access.
        
        Returns validation result with recommendations.
        """
        device, is_new = self.get_or_create_device(db, contractor_email, context, ip_address)
        
        warnings = []
        
        # Check if blocked
        if device.is_blocked:
            return DeviceValidationResult(
                is_allowed=False,
                device_id=device.id,
                trust_score=device.trust_score,
                is_new_device=is_new,
                is_blocked=True,
                warnings=["Device is blocked"],
                requires_additional_auth=False
            )
        
        # Check trust score
        if is_new:
            warnings.append("New device detected")
        
        if device.trust_score < self.TRUST_THRESHOLD_LOW:
            warnings.append("Low trust score")
        
        # Check for anomalies
        if device.failed_attempts > 3:
            warnings.append(f"Multiple failed attempts ({device.failed_attempts})")
        
        requires_passkey = (
            is_new or 
            device.trust_score < self.TRUST_THRESHOLD_REQUIRE_PASSKEY or
            device.failed_attempts > 0
        )
        
        return DeviceValidationResult(
            is_allowed=True,
            device_id=device.id,
            trust_score=device.trust_score,
            is_new_device=is_new,
            is_blocked=False,
            warnings=warnings,
            requires_additional_auth=requires_passkey and not device.is_trusted
        )
    
    def record_successful_access(self, db: Session, device_id: str):
        """Record a successful access to improve trust score."""
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if device:
            device.trust_score = min(100, device.trust_score + self.SCORE_BONUS_SUCCESSFUL_ACCESS)
            device.failed_attempts = 0  # Reset on success
            db.commit()
    
    def record_failed_access(self, db: Session, device_id: str):
        """Record a failed access attempt."""
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if device:
            device.trust_score = max(0, device.trust_score + self.SCORE_PENALTY_FAILED_ATTEMPT)
            device.failed_attempts += 1
            device.last_failed_at = datetime.now(timezone.utc)
            db.commit()
    
    def trust_device(
        self,
        db: Session,
        device_id: str,
        admin_email: str
    ) -> bool:
        """Mark a device as trusted."""
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if not device:
            return False
        
        device.is_trusted = True
        device.is_blocked = False
        device.trust_score = self.SCORE_TRUSTED_DEVICE
        device.trusted_by = admin_email
        device.trusted_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Device {device_id} marked as trusted by {admin_email}")
        return True
    
    def block_device(
        self,
        db: Session,
        device_id: str,
        admin_email: str,
        reason: str
    ) -> bool:
        """Block a device."""
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if not device:
            return False
        
        device.is_blocked = True
        device.is_trusted = False
        device.trust_score = 0
        device.blocked_by = admin_email
        device.blocked_at = datetime.now(timezone.utc)
        device.block_reason = reason
        db.commit()
        
        logger.info(f"Device {device_id} blocked by {admin_email}: {reason}")
        return True
    
    def unblock_device(
        self,
        db: Session,
        device_id: str,
        admin_email: str
    ) -> bool:
        """Unblock a device."""
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if not device:
            return False
        
        device.is_blocked = False
        device.trust_score = self.SCORE_NEW_DEVICE  # Reset to new device score
        device.blocked_by = None
        device.blocked_at = None
        device.block_reason = None
        db.commit()
        
        logger.info(f"Device {device_id} unblocked by {admin_email}")
        return True
    
    def get_devices_for_contractor(
        self,
        db: Session,
        contractor_email: str
    ) -> list[DeviceInfo]:
        """Get all devices for a contractor."""
        return db.query(DeviceInfo).filter(
            DeviceInfo.contractor_email == contractor_email
        ).order_by(DeviceInfo.last_seen.desc()).all()
    
    def get_all_devices(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        blocked_only: bool = False
    ) -> list[DeviceInfo]:
        """Get all devices with optional filtering."""
        query = db.query(DeviceInfo)
        if blocked_only:
            query = query.filter(DeviceInfo.is_blocked == True)
        return query.order_by(DeviceInfo.last_seen.desc()).offset(skip).limit(limit).all()


# Singleton instance
_device_service = None

def get_device_service() -> DeviceService:
    """Get singleton device service instance."""
    global _device_service
    if _device_service is None:
        _device_service = DeviceService()
    return _device_service
