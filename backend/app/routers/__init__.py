"""Contractor Vault - Routers Package"""
from app.routers.access import router as access_router
from app.routers.credentials import router as credentials_router
from app.routers.audit import router as audit_router
from app.routers.analytics import router as analytics_router
from app.routers.activity import router as activity_router
from app.routers.email import router as email_router
from app.routers.contractor import router as contractor_router

__all__ = [
    "access_router", "credentials_router", "audit_router", 
    "analytics_router", "activity_router", "email_router", "contractor_router"
]




