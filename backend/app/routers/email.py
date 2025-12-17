"""
Email Router - Shadow IT Detection API
Endpoints for email OAuth and signup detection.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.detected_signup import DetectedSignup, SignupStatus
from app.services.email_scanner import get_email_scanner, EmailScannerService
from app.services.discord_webhook import get_discord_service

logger = logging.getLogger("contractor_vault.email")

router = APIRouter(prefix="/api/email", tags=["Email Monitoring"])


# ===== Schemas =====

class MonitoredEmailCreate(BaseModel):
    """Request to add an email for monitoring."""
    email: EmailStr
    contractor_name: Optional[str] = None


class DetectionResponse(BaseModel):
    """A detected signup for API response."""
    id: str
    contractor_email: str
    service_name: str
    service_domain: Optional[str]
    email_subject: str
    email_from: Optional[str]
    email_date: datetime
    detected_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class DismissRequest(BaseModel):
    """Request to dismiss a detection."""
    admin_email: str
    notes: Optional[str] = None


class ManualDetectionRequest(BaseModel):
    """Request to manually add a detection."""
    contractor_email: EmailStr
    service_name: str
    service_domain: Optional[str] = None
    notes: Optional[str] = None


# ===== Endpoints =====

@router.get("/detections/{contractor_email}", response_model=list[DetectionResponse])
async def get_detections(
    contractor_email: str,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """
    Get all detected signups for a contractor.
    
    Shows services they've signed up for using company email.
    """
    query = db.query(DetectedSignup).filter(
        DetectedSignup.contractor_email == contractor_email
    )
    
    if status_filter:
        query = query.filter(DetectedSignup.status == status_filter)
    
    detections = query.order_by(DetectedSignup.detected_at.desc()).all()
    return detections


@router.get("/detections", response_model=list[DetectionResponse])
async def get_all_detections(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """
    Get all detected signups across all contractors.
    
    Used by the dashboard to show Shadow IT overview.
    """
    query = db.query(DetectedSignup)
    
    if status_filter:
        query = query.filter(DetectedSignup.status == status_filter)
    
    detections = query.order_by(DetectedSignup.detected_at.desc()).limit(limit).all()
    return detections


@router.post("/detections/dismiss/{detection_id}")
async def dismiss_detection(
    detection_id: str,
    payload: DismissRequest,
    db: Session = Depends(get_db),
):
    """
    Dismiss a detection (admin reviewed and approved).
    """
    detection = db.query(DetectedSignup).filter(
        DetectedSignup.id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    detection.status = SignupStatus.DISMISSED.value
    detection.dismissed_at = datetime.now(timezone.utc)
    detection.dismissed_by = payload.admin_email
    if payload.notes:
        detection.notes = payload.notes
    
    db.commit()
    
    logger.info(f"Detection {detection_id} dismissed by {payload.admin_email}")
    
    return {"success": True, "message": "Detection dismissed"}


@router.post("/detections/manual", response_model=DetectionResponse)
async def add_manual_detection(
    payload: ManualDetectionRequest,
    db: Session = Depends(get_db),
):
    """
    Manually add a detected signup.
    
    Use this when you know a contractor signed up for a service
    but it wasn't detected automatically.
    """
    detection = DetectedSignup(
        contractor_email=payload.contractor_email,
        service_name=payload.service_name,
        service_domain=payload.service_domain,
        email_subject="[Manual Entry]",
        email_date=datetime.now(timezone.utc),
        detection_type="manual",
        notes=payload.notes,
    )
    
    db.add(detection)
    db.commit()
    db.refresh(detection)
    
    logger.info(f"Manual detection added: {payload.contractor_email} - {payload.service_name}")
    
    # Send Discord notification
    discord = get_discord_service()
    if discord.enabled:
        await discord.notify_shadow_it_detection(
            contractor_email=payload.contractor_email,
            service_name=payload.service_name,
            detection_type="Manual Entry",
            subject=payload.notes or "Manually added by admin",
        )
    
    return detection


@router.get("/summary/{contractor_email}")
async def get_contractor_summary(
    contractor_email: str,
    db: Session = Depends(get_db),
):
    """
    Get Shadow IT summary for a contractor.
    
    Returns count of detected services by status.
    """
    active_count = db.query(DetectedSignup).filter(
        DetectedSignup.contractor_email == contractor_email,
        DetectedSignup.status == SignupStatus.ACTIVE.value
    ).count()
    
    dismissed_count = db.query(DetectedSignup).filter(
        DetectedSignup.contractor_email == contractor_email,
        DetectedSignup.status == SignupStatus.DISMISSED.value
    ).count()
    
    # Get list of active services
    active_services = db.query(DetectedSignup.service_name).filter(
        DetectedSignup.contractor_email == contractor_email,
        DetectedSignup.status == SignupStatus.ACTIVE.value
    ).distinct().all()
    
    return {
        "contractor_email": contractor_email,
        "active_detections": active_count,
        "dismissed_detections": dismissed_count,
        "total_detections": active_count + dismissed_count,
        "active_services": [s[0] for s in active_services],
        "warning_level": "high" if active_count > 5 else "medium" if active_count > 2 else "low"
    }


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    """
    Get overall Shadow IT dashboard summary.
    
    Shows top offenders and service popularity.
    """
    from sqlalchemy import func
    
    # Count by contractor
    contractor_counts = db.query(
        DetectedSignup.contractor_email,
        func.count(DetectedSignup.id).label("count")
    ).filter(
        DetectedSignup.status == SignupStatus.ACTIVE.value
    ).group_by(
        DetectedSignup.contractor_email
    ).order_by(
        func.count(DetectedSignup.id).desc()
    ).limit(10).all()
    
    # Count by service
    service_counts = db.query(
        DetectedSignup.service_name,
        func.count(DetectedSignup.id).label("count")
    ).filter(
        DetectedSignup.status == SignupStatus.ACTIVE.value
    ).group_by(
        DetectedSignup.service_name
    ).order_by(
        func.count(DetectedSignup.id).desc()
    ).limit(10).all()
    
    total_active = db.query(DetectedSignup).filter(
        DetectedSignup.status == SignupStatus.ACTIVE.value
    ).count()
    
    return {
        "total_active_detections": total_active,
        "top_contractors": [
            {"email": c.contractor_email, "count": c.count}
            for c in contractor_counts
        ],
        "popular_services": [
            {"service": s.service_name, "count": s.count}
            for s in service_counts
        ]
    }


# OAuth endpoints would go here - requires Google Cloud Console setup
# @router.get("/connect/google")
# @router.get("/callback/google")
