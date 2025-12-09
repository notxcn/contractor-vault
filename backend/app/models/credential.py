"""
Contractor Vault - Credential Model
Stores encrypted credentials with full audit trail
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, LargeBinary, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.session_token import SessionToken


class Credential(Base):
    """
    Credential model for storing encrypted service credentials.
    
    SOC2 Requirements:
    - Password is stored encrypted (Fernet symmetric encryption)
    - Full audit trail via created_by and timestamps
    - UUID primary key for non-sequential IDs
    """
    __tablename__ = "credentials"
    
    # Primary key as UUID string for cross-database compatibility
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Credential metadata
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Friendly name for the credential (e.g., 'AWS Console')"
    )
    
    target_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Target URL where credential is used"
    )
    
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Username/email for the credential"
    )
    
    # Encrypted password - stored as binary (Fernet output)
    encrypted_password: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="Fernet encrypted password"
    )
    
    # Optional notes (also encrypted in a real production system)
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about the credential"
    )
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Admin email who created this credential"
    )
    
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
    
    # Soft delete support
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="Soft delete flag"
    )
    
    # Note: relationship to session_tokens removed (no FK constraint)
    
    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, name='{self.name}', url='{self.target_url}')>"
