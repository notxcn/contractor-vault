"""
Contractor Vault - Analytics Router
Provides aggregated statistics and trends for the admin dashboard
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models import SessionToken, AuditLog, Credential, AuditAction

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get a summary of key metrics for the dashboard.
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Token stats
    total_tokens = db.query(SessionToken).count()
    active_tokens = db.query(SessionToken).filter(
        SessionToken.is_revoked == False,
        SessionToken.expires_at > now
    ).count()
    revoked_tokens = db.query(SessionToken).filter(
        SessionToken.is_revoked == True
    ).count()
    
    # Credential stats
    total_credentials = db.query(Credential).filter(Credential.is_active == True).count()
    
    # Activity stats (last 24h)
    grants_24h = db.query(AuditLog).filter(
        AuditLog.action == AuditAction.GRANT_ACCESS,
        AuditLog.timestamp >= last_24h
    ).count()
    
    injections_24h = db.query(AuditLog).filter(
        AuditLog.action == AuditAction.INJECTION_SUCCESS,
        AuditLog.timestamp >= last_24h
    ).count()
    
    revokes_24h = db.query(AuditLog).filter(
        AuditLog.action == AuditAction.REVOKE_ACCESS,
        AuditLog.timestamp >= last_24h
    ).count()
    
    return {
        "tokens": {
            "total": total_tokens,
            "active": active_tokens,
            "revoked": revoked_tokens,
            "expired": total_tokens - active_tokens - revoked_tokens,
        },
        "credentials": {
            "total": total_credentials,
        },
        "activity_24h": {
            "grants": grants_24h,
            "injections": injections_24h,
            "revokes": revokes_24h,
        },
    }


@router.get("/top-contractors")
async def get_top_contractors(
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get most active contractors by token count.
    """
    results = db.query(
        SessionToken.contractor_email,
        func.count(SessionToken.id).label("token_count"),
        func.sum(SessionToken.use_count).label("total_uses"),
    ).group_by(
        SessionToken.contractor_email
    ).order_by(
        desc("token_count")
    ).limit(limit).all()
    
    return [
        {
            "email": r.contractor_email,
            "token_count": r.token_count,
            "total_uses": r.total_uses or 0,
        }
        for r in results
    ]


@router.get("/activity-timeline")
async def get_activity_timeline(
    db: Session = Depends(get_db),
    days: int = 7
):
    """
    Get daily activity counts for the last N days.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Get all logs in range
    logs = db.query(AuditLog).filter(
        AuditLog.timestamp >= start_date
    ).all()
    
    # Group by day
    daily_stats = {}
    for i in range(days + 1):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_stats[date] = {"grants": 0, "injections": 0, "revokes": 0}
    
    for log in logs:
        date = log.timestamp.strftime("%Y-%m-%d")
        if date in daily_stats:
            if log.action == AuditAction.GRANT_ACCESS:
                daily_stats[date]["grants"] += 1
            elif log.action == AuditAction.INJECTION_SUCCESS:
                daily_stats[date]["injections"] += 1
            elif log.action == AuditAction.REVOKE_ACCESS:
                daily_stats[date]["revokes"] += 1
    
    return [
        {"date": date, **stats}
        for date, stats in sorted(daily_stats.items())
    ]


@router.get("/recent-activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get the most recent audit log entries.
    """
    logs = db.query(AuditLog).order_by(
        desc(AuditLog.timestamp)
    ).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "actor": log.actor,
            "action": log.action.value,
            "target": log.target_resource,
            "description": log.description,
        }
        for log in logs
    ]
