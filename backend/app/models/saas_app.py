"""
Contractor Vault - SaaS App Model
Catalog of known SaaS applications for shadow IT detection
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskLevel(str, enum.Enum):
    """Risk levels for SaaS applications."""
    LOW = "low"           # Well-known, trusted apps
    MEDIUM = "medium"     # Generally safe but worth monitoring
    HIGH = "high"         # Potential data exposure risk
    CRITICAL = "critical" # Known security issues or data harvesting


class AppCategory(str, enum.Enum):
    """Categories for SaaS applications."""
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


class SaaSApp(Base):
    """
    Catalog of known SaaS applications.
    
    Used for:
    - Categorizing detected signups
    - Risk scoring
    - Policy enforcement
    - Compliance reporting
    """
    __tablename__ = "saas_apps"
    
    __table_args__ = (
        Index("ix_saas_apps_domain", "domain"),
        Index("ix_saas_apps_risk_level", "risk_level"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # App identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Display name of the app (e.g., Slack, Notion)"
    )
    
    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Primary domain (e.g., slack.com)"
    )
    
    # Additional domains this app uses
    alt_domains: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated alternative domains"
    )
    
    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AppCategory.OTHER.value,
        comment="App category"
    )
    
    # Risk assessment
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RiskLevel.MEDIUM.value,
        comment="Risk level: low, medium, high, critical"
    )
    
    risk_score: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Numeric risk score 0-100"
    )
    
    risk_factors: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Explanation of risk factors"
    )
    
    # App details
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Brief description of the app"
    )
    
    logo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="URL to app logo"
    )
    
    website: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Official website URL"
    )
    
    # Compliance
    has_soc2: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether app has SOC 2 certification"
    )
    
    has_gdpr: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether app is GDPR compliant"
    )
    
    has_hipaa: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether app is HIPAA compliant"
    )
    
    # Organization policy
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this app is approved for use"
    )
    
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this app is banned"
    )
    
    policy_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Admin notes about this app's policy"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    def __repr__(self) -> str:
        return f"<SaaSApp(name={self.name}, risk={self.risk_level}, approved={self.is_approved})>"


# Pre-populate with common apps
KNOWN_SAAS_APPS = [
    {"name": "Slack", "domain": "slack.com", "category": "communication", "risk_level": "low", "risk_score": 20, "has_soc2": True},
    {"name": "Notion", "domain": "notion.so", "category": "productivity", "risk_level": "low", "risk_score": 25, "has_soc2": True},
    {"name": "Trello", "domain": "trello.com", "category": "productivity", "risk_level": "low", "risk_score": 20, "has_soc2": True},
    {"name": "Canva", "domain": "canva.com", "category": "design", "risk_level": "low", "risk_score": 30},
    {"name": "Figma", "domain": "figma.com", "category": "design", "risk_level": "low", "risk_score": 25, "has_soc2": True},
    {"name": "GitHub", "domain": "github.com", "category": "development", "risk_level": "low", "risk_score": 20, "has_soc2": True},
    {"name": "GitLab", "domain": "gitlab.com", "category": "development", "risk_level": "low", "risk_score": 25, "has_soc2": True},
    {"name": "Dropbox", "domain": "dropbox.com", "category": "storage", "risk_level": "medium", "risk_score": 40, "has_soc2": True},
    {"name": "Google Drive", "domain": "drive.google.com", "category": "storage", "risk_level": "low", "risk_score": 20, "has_soc2": True},
    {"name": "ChatGPT", "domain": "chat.openai.com", "category": "ai", "risk_level": "high", "risk_score": 70, "risk_factors": "Data sent to AI model may be used for training"},
    {"name": "Claude", "domain": "claude.ai", "category": "ai", "risk_level": "medium", "risk_score": 50, "has_soc2": True},
    {"name": "Zoom", "domain": "zoom.us", "category": "communication", "risk_level": "low", "risk_score": 25, "has_soc2": True},
    {"name": "Discord", "domain": "discord.com", "category": "communication", "risk_level": "medium", "risk_score": 45, "risk_factors": "Consumer app, limited enterprise controls"},
    {"name": "WeTransfer", "domain": "wetransfer.com", "category": "storage", "risk_level": "high", "risk_score": 65, "risk_factors": "Files accessible via public links"},
    {"name": "Pastebin", "domain": "pastebin.com", "category": "other", "risk_level": "critical", "risk_score": 85, "risk_factors": "Public by default, data exposure risk"},
]
