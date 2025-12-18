"""
Contractor Vault - Audit Log Model
Immutable audit trail for SOC2 compliance
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from sqlalchemy import String, DateTime, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.sqlite import JSON

from app.database import Base


class AuditAction(str, Enum):
    """
    Enumeration of all auditable actions in the system.
    SOC2 Requirement: All sensitive operations must be logged.
    """
    GRANT_ACCESS = "GRANT_ACCESS"           # Admin grants access to contractor
    REVOKE_ACCESS = "REVOKE_ACCESS"         # Admin revokes access
    INJECTION_SUCCESS = "INJECTION_SUCCESS" # Credential successfully injected
    SESSION_EXPIRED = "SESSION_EXPIRED"     # Token expired naturally
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"   # New credential added
    CREDENTIAL_UPDATED = "CREDENTIAL_UPDATED"   # Credential modified
    CREDENTIAL_DELETED = "CREDENTIAL_DELETED"   # Credential removed
    LOGIN_SUCCESS = "LOGIN_SUCCESS"         # Admin login
    LOGIN_FAILURE = "LOGIN_FAILURE"         # Failed login attempt
    TOKEN_VALIDATED = "TOKEN_VALIDATED"     # Token validation check
    SECURITY_ALERT = "SECURITY_ALERT"       # Security policy violation (e.g. IP mismatch)


class AuditLog(Base):
    """
    Immutable audit log for compliance tracking.
    
    SOC2 Requirements:
    - All entries are immutable (no update/delete operations)
    - Timestamps in UTC ISO 8601 format
    - IP address tracking for forensics
    - Extensible metadata for context
    
    Design Notes:
    - UUID primary key prevents enumeration attacks
    - Indexed on timestamp and actor for efficient reporting
    - JSON metadata allows flexible context storage
    """
    __tablename__ = "audit_logs"
    
    # Indexes for reporting queries
    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_actor", "actor"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_target_resource", "target_resource"),
    )
    
    # UUID primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for audit entry"
    )
    
    # Timestamp in UTC - ISO 8601 compliant
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When the action occurred (UTC)"
    )
    
    # Actor - who performed the action
    actor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email of admin or contractor who performed the action"
    )
    
    # Action type - what happened
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        comment="Type of action performed"
    )
    
    # Target resource - what was affected
    target_resource: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Resource affected (e.g., 'aws.amazon.com', credential ID)"
    )
    
    # IP address - captured from request for forensics
    ip_address: Mapped[str] = mapped_column(
        String(45),  # IPv6 max length
        nullable=False,
        comment="IP address of the requester"
    )
    
    # Extensible metadata as JSON
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Additional context (browser version, user agent, etc.)"
    )
    
    # Optional description for human-readable context
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of the action"
    )
    
    def to_csv_row(self) -> dict[str, str]:
        """Convert audit log entry to CSV-friendly dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action.value,
            "target_resource": self.target_resource,
            "ip_address": self.ip_address,
            "description": self.description or "",
            "extra_data": str(self.extra_data) if self.extra_data else "",
        }
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, "
            f"action={self.action.value}, "
            f"actor='{self.actor}', "
            f"timestamp={self.timestamp.isoformat()})>"
        )
