"""
Contractor Vault - Passkey Credential Model
WebAuthn/FIDO2 credentials for passwordless authentication
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, LargeBinary, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PasskeyCredential(Base):
    """
    Stores WebAuthn credentials for contractors.
    
    Enables passwordless authentication using biometrics (Face ID, Touch ID, 
    Windows Hello) or security keys.
    """
    __tablename__ = "passkey_credentials"
    
    __table_args__ = (
        Index("ix_passkey_contractor_email", "contractor_email"),
        Index("ix_passkey_credential_id", "credential_id"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Which contractor owns this passkey
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email of the contractor who registered this passkey"
    )
    
    # WebAuthn credential ID (base64url encoded)
    credential_id: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        comment="Unique credential ID from authenticator"
    )
    
    # Public key (stored as bytes)
    public_key: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="COSE public key from registration"
    )
    
    # Sign count for replay attack prevention
    sign_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Signature counter to detect cloned authenticators"
    )
    
    # AAGUID for authenticator identification
    aaguid: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Authenticator Attestation GUID"
    )
    
    # Human-readable device name
    device_name: Mapped[str] = mapped_column(
        String(255),
        default="Unknown Device",
        nullable=False,
        comment="User-provided name for this passkey"
    )
    
    # Credential type (platform vs cross-platform)
    credential_type: Mapped[str] = mapped_column(
        String(50),
        default="platform",
        nullable=False,
        comment="Type: platform (biometric) or cross-platform (security key)"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this passkey is active"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful authentication"
    )
    
    def __repr__(self) -> str:
        return f"<PasskeyCredential(contractor={self.contractor_email}, device={self.device_name})>"


class PasskeyChallenge(Base):
    """
    Temporary storage for WebAuthn challenges.
    
    Challenges are single-use and time-limited to prevent replay attacks.
    """
    __tablename__ = "passkey_challenges"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Challenge bytes (base64url encoded)
    challenge: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="Random challenge for WebAuthn ceremony"
    )
    
    # What this challenge is for
    challenge_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: registration or authentication"
    )
    
    # Who this challenge is for
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email of contractor this challenge is for"
    )
    
    # Token being claimed (for auth challenges)
    token_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Token ID if this is for claiming a session"
    )
    
    # Validity
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Challenge expiration (usually 5 minutes)"
    )
    
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this challenge has been consumed"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    def is_valid(self) -> bool:
        """Check if challenge is still valid."""
        if self.is_used:
            return False
        return datetime.now(timezone.utc) < self.expires_at
