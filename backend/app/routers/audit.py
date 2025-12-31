"""
Contractor Vault - Audit Router
Audit log querying and CSV export endpoints
"""
import logging
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.models.audit_log import AuditAction
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.services.audit_service import AuditService
from app.routers.auth import require_auth
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Dependency for audit service."""
    return AuditService(db)


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="Query audit logs"
)
async def list_audit_logs(
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    current_user: User = Depends(require_auth),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Start of date range"),
    end_date: Optional[datetime] = Query(None, description="End of date range"),
    limit: int = Query(100, le=1000, description="Maximum results"),
):
    """
    Query audit logs for the current authenticated user.
    Users can only see logs where they are the actor.
    
    Supports filtering by:
    - Action type (GRANT_ACCESS, REVOKE_ACCESS, etc.)
    - Date range
    """
    # Always filter by current user's email - users only see their own activity
    logs = audit_service.get_logs_by_actor(
        actor=current_user.email,
        start_date=start_date,
        end_date=end_date,
        action_filter=action
    )
    
    return AuditLogListResponse(
        logs=logs[:limit],
        total=len(logs)
    )


@router.get(
    "/export-logs",
    summary="Export audit logs as CSV",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV file with audit log data"
        }
    }
)
async def export_logs(
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    contractor_email: Optional[str] = Query(
        None,
        description="Filter by contractor email for compliance report"
    ),
    start_date: Optional[datetime] = Query(None, description="Start of date range"),
    end_date: Optional[datetime] = Query(None, description="End of date range"),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
):
    """
    Export audit logs as CSV for compliance reporting.
    
    SOC2 Requirement: Ability to generate audit reports on demand.
    
    Returns a downloadable CSV file with columns:
    - id, timestamp, actor, action, target_resource, ip_address, description, metadata
    """
    if contractor_email:
        logs = audit_service.get_logs_by_actor(
            actor=contractor_email,
            start_date=start_date,
            end_date=end_date,
            action_filter=action
        )
    else:
        # Get all logs within date range
        logs = audit_service.get_recent_logs(limit=10000)
        
        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]
        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]
        if action:
            logs = [log for log in logs if log.action == action]
    
    # Generate CSV
    csv_content = audit_service.export_to_csv(logs)
    
    # Create filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_log_export_{timestamp}.csv"
    
    if contractor_email:
        # Sanitize email for filename
        safe_email = contractor_email.replace("@", "_at_").replace(".", "_")
        filename = f"audit_log_{safe_email}_{timestamp}.csv"
    
    logger.info(f"Exported {len(logs)} audit log entries to CSV")
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Get a specific audit log entry"
)
async def get_audit_log(
    log_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Get a specific audit log entry by ID."""
    from app.models import AuditLog
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found"
        )
    
    return log
