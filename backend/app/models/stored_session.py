"""
Session model for storing authenticated browser sessions (cookies)
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StoredSession(Base):
    """
    Model for storing encrypted browser sessions (cookies).
    
    This allows admins to share authenticated sessions with contractors,
    bypassing 2FA since the session is already authenticated.
    """
    __tablename__ = "stored_sessions"
    
    # Primary key - UUID for security
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Session metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Encrypted cookie data (JSON string, encrypted)
    encrypted_cookies: Mapped[bytes] = mapped_column(
        Text,  # Store as base64 encoded encrypted blob
        nullable=False
    )
    
    # Cookie count for display purposes
    cookie_count: Mapped[int] = mapped_column(default=0)
    
    # Audit fields
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Soft delete
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<StoredSession(id={self.id}, name={self.name}, domain={self.target_domain})>"
