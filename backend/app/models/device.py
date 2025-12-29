"""
Contractor Vault - Device Info Model
Device fingerprinting and trust management for Zero Trust security
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Integer, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeviceInfo(Base):
    """
    Tracks devices that access Contractor Vault.
    
    Enables Zero Trust security by:
    - Fingerprinting devices
    - Tracking device trust status
    - Detecting anomalous access patterns
    """
    __tablename__ = "device_info"
    
    __table_args__ = (
        Index("ix_device_contractor_email", "contractor_email"),
        Index("ix_device_fingerprint", "fingerprint"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Device fingerprint (hash of device characteristics)
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of device characteristics"
    )
    
    # Owner
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email of contractor using this device"
    )
    
    # Device details
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full user agent string"
    )
    
    browser: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Browser name and version (e.g., Chrome 120)"
    )
    
    browser_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Browser version"
    )
    
    os: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Operating system (e.g., Windows 11, macOS 14)"
    )
    
    os_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="OS version"
    )
    
    device_type: Mapped[str] = mapped_column(
        String(50),
        default="desktop",
        nullable=False,
        comment="Type: desktop, mobile, tablet"
    )
    
    # Location (from IP geolocation)
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="Last known IP address"
    )
    
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Country from IP geolocation"
    )
    
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="City from IP geolocation"
    )
    
    # Trust status
    is_trusted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this device is trusted by admin"
    )
    
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this device is blocked"
    )
    
    trust_score: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Trust score 0-100 (higher = more trusted)"
    )
    
    # Usage tracking
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    access_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of times this device accessed the system"
    )
    
    # Anomaly tracking
    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of failed access attempts"
    )
    
    last_failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last failed access attempt"
    )
    
    # Admin actions
    trusted_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Admin who marked device as trusted"
    )
    
    trusted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When device was marked trusted"
    )
    
    blocked_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Admin who blocked this device"
    )
    
    blocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When device was blocked"
    )
    
    block_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for blocking"
    )
    
    def __repr__(self) -> str:
        status = "trusted" if self.is_trusted else ("blocked" if self.is_blocked else "unknown")
        return f"<DeviceInfo(contractor={self.contractor_email}, status={status}, score={self.trust_score})>"
