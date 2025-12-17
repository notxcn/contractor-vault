"""
Detected Signup Model - Shadow IT Detection
Stores detected service signups from contractor emails.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class SignupStatus(str, enum.Enum):
    """Status of a detected signup."""
    ACTIVE = "active"          # Detected, needs attention
    DISMISSED = "dismissed"     # Admin dismissed
    REVOKED = "revoked"        # Access was revoked


class DetectedSignup(Base):
    """
    Tracks SaaS signups detected from contractor emails.
    
    When a contractor uses company email to sign up for external
    services, we detect and log it here for admin review.
    """
    __tablename__ = "detected_signups"
    
    __table_args__ = (
        Index("ix_detected_signups_contractor", "contractor_email"),
        Index("ix_detected_signups_status", "status"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Which contractor's email
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email address being monitored"
    )
    
    # Detected service
    service_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the service (e.g., 'Canva', 'Trello')"
    )
    
    service_domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Domain of the service (e.g., 'canva.com')"
    )
    
    # Email that triggered detection
    email_subject: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Subject line that matched our pattern"
    )
    
    email_from: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Sender email address"
    )
    
    email_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the email was received"
    )
    
    # Detection metadata
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When we detected this signup"
    )
    
    detection_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="email_subject",
        comment="How it was detected: email_subject, email_body, etc."
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SignupStatus.ACTIVE.value,
        comment="Current status: active, dismissed, revoked"
    )
    
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this was dismissed"
    )
    
    dismissed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Admin who dismissed this"
    )
    
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Admin notes about this signup"
    )
    
    def __repr__(self) -> str:
        return f"<DetectedSignup(contractor={self.contractor_email}, service={self.service_name}, status={self.status})>"
