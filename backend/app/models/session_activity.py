"""
Session Activity Model - URL Traversal Logging
Tracks every URL visited during an active session for forensic auditing.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionActivity(Base):
    """
    Tracks URL navigation during an active contractor session.
    
    SOC2 Requirements:
    - Complete audit trail of contractor activity
    - Immutable logging (no updates/deletes)
    - Linked to specific session tokens
    """
    __tablename__ = "session_activities"
    
    __table_args__ = (
        Index("ix_session_activities_token_id", "session_token_id"),
        Index("ix_session_activities_timestamp", "timestamp"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Link to session token
    session_token_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("session_tokens.id"),
        nullable=False,
        comment="The session token this activity belongs to"
    )
    
    # Activity data
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full URL visited"
    )
    
    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Page title"
    )
    
    # Navigation metadata
    transition_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="How user got here: link, typed, reload, etc."
    )
    
    referrer_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Previous page URL"
    )
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When this URL was visited"
    )
    
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Time spent on this page in milliseconds"
    )
    
    # Relationship
    session_token = relationship("SessionToken", backref="activities")
    
    def __repr__(self) -> str:
        return f"<SessionActivity(token={self.session_token_id[:8]}..., url={self.url[:50]})>"
