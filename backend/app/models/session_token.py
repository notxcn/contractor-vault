"""
Contractor Vault - Session Token Model
Time-bombed access tokens linking contractors to credentials
"""
import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.credential import Credential


def generate_secure_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)


class SessionToken(Base):
    """
    Session token model for temporary contractor access.
    
    SOC2 Requirements:
    - Time-limited access (expires_at)
    - Revocation support (is_revoked)
    - Full audit trail
    - Cryptographically secure token generation
    """
    __tablename__ = "session_tokens"
    
    # Indexes for performance on common queries
    __table_args__ = (
        Index("ix_session_tokens_token", "token"),
        Index("ix_session_tokens_contractor_email", "contractor_email"),
        Index("ix_session_tokens_expires_at", "expires_at"),
    )
    
    # Primary key as UUID string
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # The actual token used for access - URL-safe random string
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=generate_secure_token,
        comment="Unique access token for contractor"
    )
    
    # Reference to credential or stored session (no FK constraint for flexibility)
    credential_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="ID of the credential or stored session being accessed"
    )
    
    # Contractor identification
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email of the contractor granted access"
    )

    # IP Whitelisting
    allowed_ip: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="Optional IP address restriction"
    )
    
    # Token validity
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiration timestamp (UTC)"
    )
    
    # Revocation support
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether token has been manually revoked"
    )
    
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the token was revoked"
    )
    
    revoked_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Admin who revoked the token"
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    created_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Admin who created this token"
    )
    
    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this token was used"
    )
    
    use_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of times token was used"
    )
    
    # Note: No relationship defined since credential_id can reference
    # either credentials or stored_sessions tables
    
    def is_valid(self) -> bool:
        """Check if token is currently valid (not expired and not revoked)."""
        if self.is_revoked:
            return False
        return datetime.now(timezone.utc) < self.expires_at
    
    def __repr__(self) -> str:
        status = "valid" if self.is_valid() else "invalid"
        return f"<SessionToken(id={self.id}, contractor='{self.contractor_email}', status={status})>"
