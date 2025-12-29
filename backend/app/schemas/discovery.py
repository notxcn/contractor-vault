"""
Contractor Vault - Discovery Schemas
Request/response models for SaaS discovery and shadow IT detection
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RiskLevelEnum(str, Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppCategoryEnum(str, Enum):
    """App categories."""
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    DESIGN = "design"
    FINANCE = "finance"
    MARKETING = "marketing"
    STORAGE = "storage"
    SECURITY = "security"
    ANALYTICS = "analytics"
    AI = "ai"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class SaaSAppInfo(BaseModel):
    """SaaS app information."""
    id: str
    name: str
    domain: str
    category: str
    risk_level: str
    risk_score: int
    description: Optional[str]
    has_soc2: bool
    has_gdpr: bool
    is_approved: bool
    is_banned: bool

    class Config:
        from_attributes = True


class SaaSAppCreate(BaseModel):
    """Request to add a new SaaS app to catalog."""
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    category: AppCategoryEnum = AppCategoryEnum.OTHER
    risk_level: RiskLevelEnum = RiskLevelEnum.MEDIUM
    risk_score: int = Field(default=50, ge=0, le=100)
    risk_factors: Optional[str] = None
    description: Optional[str] = None


class SaaSAppUpdate(BaseModel):
    """Request to update a SaaS app."""
    risk_level: Optional[RiskLevelEnum] = None
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    is_approved: Optional[bool] = None
    is_banned: Optional[bool] = None
    policy_notes: Optional[str] = None


class DetectedAppInfo(BaseModel):
    """Detected app usage info."""
    id: str
    contractor_email: str
    service_name: str
    service_domain: Optional[str]
    email_subject: str
    detected_at: datetime
    status: str
    risk_level: Optional[str] = None
    risk_score: Optional[int] = None
    is_approved: bool = False

    class Config:
        from_attributes = True


class DiscoveryReport(BaseModel):
    """Summary report of discovered SaaS usage."""
    total_apps_detected: int
    unique_apps: int
    high_risk_apps: int
    unapproved_apps: int
    contractors_with_signups: int
    apps_by_category: dict[str, int]
    apps_by_risk: dict[str, int]
    recent_detections: list[DetectedAppInfo]


class AppAuthorizationRequest(BaseModel):
    """Request to authorize/ban an app."""
    action: str = Field(..., pattern="^(approve|ban|reset)$")
    admin_email: str
    policy_notes: Optional[str] = None


class ContractorAppUsage(BaseModel):
    """App usage for a specific contractor."""
    contractor_email: str
    apps_used: list[DetectedAppInfo]
    total_apps: int
    high_risk_count: int
    unapproved_count: int
