"""
Contractor Vault - Audit Service
SOC2-compliant audit logging service
"""
import logging
import csv
import io
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating and querying audit log entries.
    
    SOC2 Requirements:
    - All entries are write-only (no updates/deletes)
    - Automatic timestamp in UTC
    - IP address capture for forensics
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self._db = db
    
    def log(
        self,
        actor: str,
        action: AuditAction,
        target_resource: str,
        ip_address: str,
        extra_data: Optional[dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            actor: Email of person performing action
            action: Type of action (from AuditAction enum)
            target_resource: What was affected
            ip_address: IP of the requester
            extra_data: Additional context (JSON-serializable)
            description: Human-readable description
            
        Returns:
            The created AuditLog entry
        """
        entry = AuditLog(
            actor=actor,
            action=action,
            target_resource=target_resource,
            ip_address=ip_address,
            extra_data=extra_data or {},
            description=description,
            timestamp=datetime.now(timezone.utc)
        )
        
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        
        # Log at appropriate level based on action type
        log_level = logging.WARNING if action == AuditAction.REVOKE_ACCESS else logging.INFO
        logger.log(
            log_level,
            f"AUDIT: {action.value} by {actor} on {target_resource} from {ip_address}"
        )
        
        return entry
    
    def get_logs_by_actor(
        self,
        actor: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_filter: Optional[AuditAction] = None
    ) -> list[AuditLog]:
        """
        Query audit logs for a specific actor.
        
        Args:
            actor: Email to filter by
            start_date: Optional start of date range
            end_date: Optional end of date range
            action_filter: Optional action type filter
            
        Returns:
            List of matching AuditLog entries
        """
        query = self._db.query(AuditLog).filter(AuditLog.actor == actor)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        return query.order_by(AuditLog.timestamp.desc()).all()
    
    def get_logs_by_resource(
        self,
        target_resource: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[AuditLog]:
        """
        Query audit logs for a specific resource.
        
        Args:
            target_resource: Resource to filter by
            start_date: Optional start of date range
            end_date: Optional end of date range
            
        Returns:
            List of matching AuditLog entries
        """
        query = self._db.query(AuditLog).filter(
            AuditLog.target_resource.contains(target_resource)
        )
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).all()
    
    def export_to_csv(self, logs: list[AuditLog]) -> str:
        """
        Export audit logs to CSV format.
        
        Args:
            logs: List of AuditLog entries to export
            
        Returns:
            CSV string content
        """
        output = io.StringIO()
        
        if not logs:
            return ""
        
        fieldnames = [
            "id", "timestamp", "actor", "action",
            "target_resource", "ip_address", "description", "metadata"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in logs:
            writer.writerow(log.to_csv_row())
        
        return output.getvalue()
    
    def get_recent_logs(self, limit: int = 100) -> list[AuditLog]:
        """
        Get most recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent AuditLog entries
        """
        return (
            self._db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
