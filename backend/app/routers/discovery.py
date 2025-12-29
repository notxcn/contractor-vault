"""
Contractor Vault - Discovery Router
SaaS app discovery and shadow IT detection endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.discovery_service import get_discovery_service, DiscoveryService
from app.models.saas_app import SaaSApp
from app.models.detected_signup import DetectedSignup
from app.schemas.discovery import (
    SaaSAppInfo,
    SaaSAppCreate,
    SaaSAppUpdate,
    DetectedAppInfo,
    DiscoveryReport,
    AppAuthorizationRequest,
    ContractorAppUsage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["SaaS Discovery"])


@router.get("/apps", response_model=list[SaaSAppInfo])
async def list_apps(
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """List all known SaaS apps."""
    apps = discovery_service.get_all_apps(db, skip, limit, risk_level)
    return [SaaSAppInfo.model_validate(app) for app in apps]


@router.post("/apps", response_model=SaaSAppInfo)
async def add_app(
    payload: SaaSAppCreate,
    db: Session = Depends(get_db)
):
    """Add a new SaaS app to the catalog."""
    # Check for duplicate
    existing = db.query(SaaSApp).filter(SaaSApp.domain == payload.domain).first()
    if existing:
        raise HTTPException(status_code=409, detail="App with this domain already exists")
    
    app = SaaSApp(
        name=payload.name,
        domain=payload.domain,
        category=payload.category.value,
        risk_level=payload.risk_level.value,
        risk_score=payload.risk_score,
        risk_factors=payload.risk_factors,
        description=payload.description
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)
    
    logger.info(f"Added SaaS app: {payload.name}")
    return SaaSAppInfo.model_validate(app)


@router.get("/apps/{app_id}", response_model=SaaSAppInfo)
async def get_app(
    app_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific app."""
    app = db.query(SaaSApp).filter(SaaSApp.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return SaaSAppInfo.model_validate(app)


@router.patch("/apps/{app_id}", response_model=SaaSAppInfo)
async def update_app(
    app_id: str,
    payload: SaaSAppUpdate,
    db: Session = Depends(get_db)
):
    """Update an app's risk or policy status."""
    app = db.query(SaaSApp).filter(SaaSApp.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    if payload.risk_level is not None:
        app.risk_level = payload.risk_level.value
    if payload.risk_score is not None:
        app.risk_score = payload.risk_score
    if payload.is_approved is not None:
        app.is_approved = payload.is_approved
    if payload.is_banned is not None:
        app.is_banned = payload.is_banned
    if payload.policy_notes is not None:
        app.policy_notes = payload.policy_notes
    
    db.commit()
    db.refresh(app)
    
    return SaaSAppInfo.model_validate(app)


@router.post("/apps/{app_id}/authorize")
async def authorize_app(
    app_id: str,
    payload: AppAuthorizationRequest,
    db: Session = Depends(get_db),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """Approve, ban, or reset an app's authorization status."""
    success = discovery_service.authorize_app(
        db=db,
        app_id=app_id,
        admin_email=payload.admin_email,
        action=payload.action,
        notes=payload.policy_notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="App not found or invalid action")
    
    return {"success": True, "message": f"App {payload.action}d successfully"}


@router.get("/report", response_model=DiscoveryReport)
async def get_discovery_report(
    db: Session = Depends(get_db),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """Get a summary report of discovered SaaS usage."""
    report_data = discovery_service.get_discovery_report(db)
    
    return DiscoveryReport(
        total_apps_detected=report_data["total_apps_detected"],
        unique_apps=report_data["unique_apps"],
        high_risk_apps=report_data["high_risk_apps"],
        unapproved_apps=report_data["unapproved_apps"],
        contractors_with_signups=report_data["contractors_with_signups"],
        apps_by_category=report_data["apps_by_category"],
        apps_by_risk=report_data["apps_by_risk"],
        recent_detections=[
            DetectedAppInfo(
                id=d.id,
                contractor_email=d.contractor_email,
                service_name=d.service_name,
                service_domain=d.service_domain,
                email_subject=d.email_subject,
                detected_at=d.detected_at,
                status=d.status
            )
            for d in report_data["recent_detections"]
        ]
    )


@router.get("/detections", response_model=list[DetectedAppInfo])
async def list_detections(
    skip: int = 0,
    limit: int = 100,
    contractor_email: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all detected signups."""
    query = db.query(DetectedSignup)
    
    if contractor_email:
        query = query.filter(DetectedSignup.contractor_email == contractor_email)
    if status:
        query = query.filter(DetectedSignup.status == status)
    
    detections = query.order_by(DetectedSignup.detected_at.desc()).offset(skip).limit(limit).all()
    
    return [
        DetectedAppInfo(
            id=d.id,
            contractor_email=d.contractor_email,
            service_name=d.service_name,
            service_domain=d.service_domain,
            email_subject=d.email_subject,
            detected_at=d.detected_at,
            status=d.status
        )
        for d in detections
    ]


@router.get("/contractor/{contractor_email}", response_model=ContractorAppUsage)
async def get_contractor_usage(
    contractor_email: str,
    db: Session = Depends(get_db),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """Get app usage for a specific contractor."""
    usage_data = discovery_service.get_contractor_app_usage(db, contractor_email)
    
    return ContractorAppUsage(
        contractor_email=contractor_email,
        apps_used=[
            DetectedAppInfo(
                id=d.id,
                contractor_email=d.contractor_email,
                service_name=d.service_name,
                service_domain=d.service_domain,
                email_subject=d.email_subject,
                detected_at=d.detected_at,
                status=d.status
            )
            for d in usage_data["apps_used"]
        ],
        total_apps=usage_data["total_apps"],
        high_risk_count=usage_data["high_risk_count"],
        unapproved_count=usage_data["unapproved_count"]
    )


@router.post("/seed")
async def seed_known_apps(
    db: Session = Depends(get_db),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """Seed the database with known SaaS apps."""
    discovery_service.seed_known_apps(db)
    return {"success": True, "message": "Known apps seeded"}


@router.post("/detections/{detection_id}/dismiss")
async def dismiss_detection(
    detection_id: str,
    admin_email: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Dismiss a detected signup."""
    from datetime import datetime, timezone
    from app.models.detected_signup import SignupStatus
    
    detection = db.query(DetectedSignup).filter(DetectedSignup.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    detection.status = SignupStatus.DISMISSED.value
    detection.dismissed_at = datetime.now(timezone.utc)
    detection.dismissed_by = admin_email
    if notes:
        detection.notes = notes
    
    db.commit()
    
    return {"success": True, "message": "Detection dismissed"}
