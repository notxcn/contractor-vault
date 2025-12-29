"""
Contractor Vault - Secret Model
Secrets management for API keys, database credentials, SSH keys, environment variables
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, LargeBinary, Boolean, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecretType(str, enum.Enum):
    """Types of secrets that can be stored."""
    API_KEY = "api_key"
    DATABASE = "database"
    SSH_KEY = "ssh_key"
    ENV_VAR = "env_var"
    OAUTH_TOKEN = "oauth_token"
    CERTIFICATE = "certificate"
    OTHER = "other"


class Secret(Base):
    """
    Stores encrypted secrets for time-limited sharing.
    
    Supports multiple secret types:
    - API keys (Stripe, AWS, etc.)
    - Database credentials
    - SSH keys
    - Environment variables
    - OAuth tokens
    - Certificates
    """
    __tablename__ = "secrets"
    
    __table_args__ = (
        Index("ix_secrets_created_by", "created_by"),
        Index("ix_secrets_type", "secret_type"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Human-readable name
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name for this secret"
    )
    
    # Secret type
    secret_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SecretType.OTHER.value,
        comment="Type of secret: api_key, database, ssh_key, env_var, etc."
    )
    
    # Encrypted secret value
    encrypted_value: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="Fernet-encrypted secret value"
    )
    
    # Optional description
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of what this secret is for"
    )
    
    # Type-specific metadata (JSON)
    # e.g., for database: {"host": "...", "port": 5432, "database": "..."}
    # e.g., for API key: {"service": "stripe", "scope": "read"}
    secret_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Type-specific metadata"
    )
    
    # Tags for organization
    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Tags for organizing secrets"
    )
    
    # Ownership
    created_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Admin who created this secret"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this secret is active"
    )
    
    # Rotation tracking
    last_rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When secret was last rotated"
    )
    
    rotation_reminder_days: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Days between rotation reminders"
    )
    
    # Expiration (for tokens that expire)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this secret expires (if applicable)"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Usage tracking
    access_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of times this secret was accessed"
    )
    
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this secret was accessed"
    )
    
    def is_expired(self) -> bool:
        """Check if this secret has expired."""
        if self.expires_at is None:
            return False
            
        expires_at = self.expires_at
        now = datetime.now(timezone.utc)
        
        if expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
            
        return now > expires_at
    
    def needs_rotation(self) -> bool:
        """Check if this secret needs rotation."""
        if self.rotation_reminder_days is None:
            return False
        if self.last_rotated_at is None:
            # Never rotated, use created_at
            last_rotation = self.created_at
        else:
            last_rotation = self.last_rotated_at
        
        from datetime import timedelta
        
        
        now = datetime.now(timezone.utc)
        if last_rotation.tzinfo is None:
            now = now.replace(tzinfo=None)
            
        return now > last_rotation + timedelta(days=self.rotation_reminder_days)
    
    def __repr__(self) -> str:
        return f"<Secret(name={self.name}, type={self.secret_type}, active={self.is_active})>"
