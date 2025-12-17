"""
Activity Router - URL Traversal Logging
Endpoints for logging and retrieving session activity.
"""
import logging
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import SessionToken, SessionActivity

logger = logging.getLogger("contractor_vault.activity")

router = APIRouter(prefix="/api/activity", tags=["Activity Logging"])


# ===== Schemas =====

class ActivityItem(BaseModel):
    """Single navigation event from the extension."""
    url: str
    title: str | None = None
    transition_type: str | None = None
    referrer_url: str | None = None
    timestamp: datetime
    duration_ms: int | None = None


class ActivityBatch(BaseModel):
    """Batch of activities sent by the extension."""
    session_token: str  # The token string (not ID)
    activities: list[ActivityItem]


class ActivityResponse(BaseModel):
    """Response for activity queries."""
    id: str
    url: str
    title: str | None
    transition_type: str | None
    timestamp: datetime
    duration_ms: int | None
    
    class Config:
        from_attributes = True


# ===== Endpoints =====

@router.post("/log", status_code=status.HTTP_201_CREATED)
async def log_activity(
    batch: ActivityBatch,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Log a batch of URL navigation events from the extension.
    
    The extension sends these periodically during an active session.
    """
    # Find the session token
    session_token = db.query(SessionToken).filter(
        SessionToken.token == batch.session_token
    ).first()
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session token not found"
        )
    
    # Check if session is still valid
    if session_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session has been revoked"
        )
    
    # Store each activity
    logged_count = 0
    for activity in batch.activities:
        # Skip duplicate URLs in quick succession (debounce)
        existing = db.query(SessionActivity).filter(
            SessionActivity.session_token_id == session_token.id,
            SessionActivity.url == activity.url,
            SessionActivity.timestamp >= activity.timestamp
        ).first()
        
        if existing:
            continue
        
        session_activity = SessionActivity(
            session_token_id=session_token.id,
            url=activity.url,
            title=activity.title,
            transition_type=activity.transition_type,
            referrer_url=activity.referrer_url,
            timestamp=activity.timestamp if activity.timestamp.tzinfo else activity.timestamp.replace(tzinfo=timezone.utc),
            duration_ms=activity.duration_ms,
        )
        db.add(session_activity)
        logged_count += 1
    
    db.commit()
    
    logger.info(f"Logged {logged_count} activities for token {batch.session_token[:10]}...")
    
    return {
        "success": True,
        "logged_count": logged_count,
        "message": f"Logged {logged_count} navigation events"
    }


@router.get("/{token_id}", response_model=list[ActivityResponse])
async def get_session_activity(
    token_id: str,
    db: Session = Depends(get_db),
    limit: int = 100,
):
    """
    Get all activity for a specific session token.
    
    Used by the dashboard to show URL traversal timeline.
    """
    # Verify token exists
    session_token = db.query(SessionToken).filter(
        SessionToken.id == token_id
    ).first()
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session token not found"
        )
    
    # Get activities ordered by timestamp
    activities = db.query(SessionActivity).filter(
        SessionActivity.session_token_id == token_id
    ).order_by(SessionActivity.timestamp.asc()).limit(limit).all()
    
    return activities


@router.get("/summary/{token_id}")
async def get_activity_summary(
    token_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a summary of session activity for quick display.
    
    Returns domains visited, page count, and duration.
    """
    session_token = db.query(SessionToken).filter(
        SessionToken.id == token_id
    ).first()
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session token not found"
        )
    
    activities = db.query(SessionActivity).filter(
        SessionActivity.session_token_id == token_id
    ).order_by(SessionActivity.timestamp.asc()).all()
    
    if not activities:
        return {
            "total_pages": 0,
            "unique_domains": [],
            "duration_seconds": 0,
            "path_summary": []
        }
    
    # Extract unique domains
    from urllib.parse import urlparse
    domains = set()
    path_summary = []
    
    for activity in activities:
        try:
            parsed = urlparse(activity.url)
            domains.add(parsed.netloc)
            # Create simplified path
            path = parsed.path[:50] + "..." if len(parsed.path) > 50 else parsed.path
            path_summary.append({
                "domain": parsed.netloc,
                "path": path,
                "title": activity.title or parsed.path,
                "timestamp": activity.timestamp.isoformat()
            })
        except:
            pass
    
    # Calculate session duration
    first_ts = activities[0].timestamp
    last_ts = activities[-1].timestamp
    duration = (last_ts - first_ts).total_seconds()
    
    return {
        "total_pages": len(activities),
        "unique_domains": list(domains),
        "duration_seconds": int(duration),
        "path_summary": path_summary[:20]  # Limit to 20 for summary
    }
