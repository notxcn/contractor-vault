"""
Contractor Vault - Discovery Service
SaaS app detection and shadow IT risk analysis
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.saas_app import SaaSApp, RiskLevel, KNOWN_SAAS_APPS
from app.models.detected_signup import DetectedSignup, SignupStatus

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Service for SaaS discovery and shadow IT detection.
    
    Handles:
    - App catalog management
    - Risk scoring
    - Detection analysis
    - Compliance reporting
    """
    
    def seed_known_apps(self, db: Session):
        """Seed the database with known SaaS apps."""
        for app_data in KNOWN_SAAS_APPS:
            existing = db.query(SaaSApp).filter(
                SaaSApp.domain == app_data["domain"]
            ).first()
            
            if not existing:
                app = SaaSApp(**app_data)
                db.add(app)
        
        db.commit()
        logger.info(f"Seeded {len(KNOWN_SAAS_APPS)} known SaaS apps")
    
    def get_or_create_app(
        self,
        db: Session,
        name: str,
        domain: str,
        category: str = "other"
    ) -> SaaSApp:
        """Get existing app or create new one."""
        app = db.query(SaaSApp).filter(SaaSApp.domain == domain).first()
        
        if not app:
            app = SaaSApp(
                name=name,
                domain=domain,
                category=category,
                risk_level=RiskLevel.MEDIUM.value,
                risk_score=50
            )
            db.add(app)
            db.commit()
            db.refresh(app)
            logger.info(f"Created new SaaS app: {name} ({domain})")
        
        return app
    
    def detect_app_from_email(
        self,
        db: Session,
        contractor_email: str,
        sender_email: str,
        subject: str,
        email_date: datetime
    ) -> Optional[DetectedSignup]:
        """
        Detect SaaS signup from email.
        
        Analyzes sender domain and subject line patterns.
        """
        # Extract domain from sender
        if "@" in sender_email:
            sender_domain = sender_email.split("@")[1].lower()
        else:
            return None
        
        # Common signup subject patterns
        signup_patterns = [
            "welcome to",
            "confirm your email",
            "verify your email",
            "activate your account",
            "complete your registration",
            "you're in",
            "get started with",
            "thanks for signing up"
        ]
        
        subject_lower = subject.lower()
        is_signup = any(pattern in subject_lower for pattern in signup_patterns)
        
        if not is_signup:
            return None
        
        # Try to match to known app
        app = db.query(SaaSApp).filter(
            SaaSApp.domain.contains(sender_domain.split(".")[0])
        ).first()
        
        # Extract service name from sender domain
        service_name = sender_domain.split(".")[0].title()
        if app:
            service_name = app.name
        
        # Check for duplicate detection
        existing = db.query(DetectedSignup).filter(
            DetectedSignup.contractor_email == contractor_email,
            DetectedSignup.service_domain == sender_domain,
            DetectedSignup.email_date == email_date
        ).first()
        
        if existing:
            return existing
        
        # Create detection record
        detection = DetectedSignup(
            contractor_email=contractor_email,
            service_name=service_name,
            service_domain=sender_domain,
            email_subject=subject,
            email_from=sender_email,
            email_date=email_date,
            detection_type="email_subject"
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        
        logger.info(f"Detected signup for {contractor_email}: {service_name}")
        return detection
    
    def get_discovery_report(self, db: Session) -> dict:
        """Generate a summary report of discovered SaaS usage."""
        # Total detections
        total = db.query(DetectedSignup).filter(
            DetectedSignup.status == SignupStatus.ACTIVE.value
        ).count()
        
        # Unique apps
        unique_apps = db.query(func.count(func.distinct(DetectedSignup.service_domain))).scalar()
        
        # Contractors with signups
        contractors = db.query(func.count(func.distinct(DetectedSignup.contractor_email))).scalar()
        
        # Apps by category (join with SaaSApp)
        apps_by_category = {}
        category_counts = db.query(
            SaaSApp.category, func.count(SaaSApp.id)
        ).group_by(SaaSApp.category).all()
        for cat, count in category_counts:
            apps_by_category[cat] = count
        
        # Apps by risk level
        apps_by_risk = {}
        risk_counts = db.query(
            SaaSApp.risk_level, func.count(SaaSApp.id)
        ).group_by(SaaSApp.risk_level).all()
        for risk, count in risk_counts:
            apps_by_risk[risk] = count
        
        # High risk app count (from detections)
        high_risk_apps = db.query(DetectedSignup).join(
            SaaSApp, SaaSApp.domain == DetectedSignup.service_domain
        ).filter(
            SaaSApp.risk_level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value])
        ).count()
        
        # Unapproved apps
        unapproved = db.query(DetectedSignup).join(
            SaaSApp, SaaSApp.domain == DetectedSignup.service_domain
        ).filter(
            SaaSApp.is_approved == False,
            SaaSApp.is_banned == False
        ).count()
        
        # Recent detections
        recent = db.query(DetectedSignup).filter(
            DetectedSignup.status == SignupStatus.ACTIVE.value
        ).order_by(DetectedSignup.detected_at.desc()).limit(10).all()
        
        return {
            "total_apps_detected": total,
            "unique_apps": unique_apps or 0,
            "high_risk_apps": high_risk_apps,
            "unapproved_apps": unapproved,
            "contractors_with_signups": contractors or 0,
            "apps_by_category": apps_by_category,
            "apps_by_risk": apps_by_risk,
            "recent_detections": recent
        }
    
    def authorize_app(
        self,
        db: Session,
        app_id: str,
        admin_email: str,
        action: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Authorize, ban, or reset an app's status.
        
        Actions: approve, ban, reset
        """
        app = db.query(SaaSApp).filter(SaaSApp.id == app_id).first()
        if not app:
            return False
        
        if action == "approve":
            app.is_approved = True
            app.is_banned = False
        elif action == "ban":
            app.is_banned = True
            app.is_approved = False
        elif action == "reset":
            app.is_approved = False
            app.is_banned = False
        else:
            return False
        
        if notes:
            app.policy_notes = notes
        
        db.commit()
        logger.info(f"App {app.name} {action}d by {admin_email}")
        return True
    
    def get_contractor_app_usage(
        self,
        db: Session,
        contractor_email: str
    ) -> dict:
        """Get app usage for a specific contractor."""
        detections = db.query(DetectedSignup).filter(
            DetectedSignup.contractor_email == contractor_email
        ).all()
        
        high_risk = 0
        unapproved = 0
        
        for detection in detections:
            app = db.query(SaaSApp).filter(
                SaaSApp.domain == detection.service_domain
            ).first()
            
            if app:
                if app.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                    high_risk += 1
                if not app.is_approved and not app.is_banned:
                    unapproved += 1
        
        return {
            "contractor_email": contractor_email,
            "apps_used": detections,
            "total_apps": len(detections),
            "high_risk_count": high_risk,
            "unapproved_count": unapproved
        }
    
    def get_all_apps(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        risk_level: Optional[str] = None
    ) -> list[SaaSApp]:
        """Get all apps from catalog."""
        query = db.query(SaaSApp)
        if risk_level:
            query = query.filter(SaaSApp.risk_level == risk_level)
        return query.order_by(SaaSApp.risk_score.desc()).offset(skip).limit(limit).all()


# Singleton instance
_discovery_service = None

def get_discovery_service() -> DiscoveryService:
    """Get singleton discovery service instance."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service
