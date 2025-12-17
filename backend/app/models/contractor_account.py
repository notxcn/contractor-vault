"""
Contractor Account Model - Agency Bridge Feature
Supports contractors having one master account linked to multiple clients.
"""
import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_magic_token():
    """Generate a secure magic link token."""
    return secrets.token_urlsafe(32)


class ContractorAccount(Base):
    """
    Master contractor account for multi-client access.
    
    Allows contractors to have one identity across
    multiple clients who use Contractor Vault.
    """
    __tablename__ = "contractor_accounts"
    
    __table_args__ = (
        Index("ix_contractor_accounts_email", "email", unique=True),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Contractor's own email (not company-provided)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Contractor's personal/business email"
    )
    
    # Profile
    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Contractor's display name"
    )
    
    # Magic link authentication
    magic_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Current magic link token"
    )
    
    magic_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When magic token expires"
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether account is active"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login"
    )
    
    # Relationships
    client_links = relationship("ClientLink", back_populates="contractor")
    
    def __repr__(self) -> str:
        return f"<ContractorAccount(email={self.email})>"


class ClientLink(Base):
    """
    Links a contractor account to a client (company using Contractor Vault).
    
    This is what enables the multi-client dropdown in the extension.
    """
    __tablename__ = "client_links"
    
    __table_args__ = (
        Index("ix_client_links_contractor", "contractor_id"),
        Index("ix_client_links_client_name", "client_name"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Which contractor
    contractor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contractor_accounts.id"),
        nullable=False
    )
    
    # Client info
    client_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the client company"
    )
    
    client_api_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="API URL if using hosted version"
    )
    
    # Invitation metadata
    invited_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Admin who sent the invitation"
    )
    
    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Link status
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    
    # Relationships
    contractor = relationship("ContractorAccount", back_populates="client_links")
    
    def __repr__(self) -> str:
        return f"<ClientLink(contractor_id={self.contractor_id}, client={self.client_name})>"
