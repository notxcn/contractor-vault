"""
Contractor Vault - Audit Log Schemas
Pydantic models for audit log API
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    """Schema for audit log API responses."""
    id: str
    timestamp: datetime
    actor: str
    action: AuditAction
    target_resource: str
    ip_address: str
    extra_data: Optional[dict[str, Any]]
    description: Optional[str]
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for listing audit logs."""
    logs: list[AuditLogResponse]
    total: int


class ExportLogsRequest(BaseModel):
    """Schema for requesting audit log export."""
    contractor_email: Optional[EmailStr] = Field(
        None,
        description="Filter by contractor email"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start of date range filter"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End of date range filter"
    )
    action_filter: Optional[AuditAction] = Field(
        None,
        description="Filter by action type"
    )
