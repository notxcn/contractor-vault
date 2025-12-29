"""Contractor Vault - Routers Package"""
from app.routers.access import router as access_router
from app.routers.credentials import router as credentials_router
from app.routers.audit import router as audit_router
from app.routers.analytics import router as analytics_router
from app.routers.activity import router as activity_router
from app.routers.email import router as email_router
from app.routers.contractor import router as contractor_router
from app.routers.passkey import router as passkey_router
from app.routers.device import router as device_router
from app.routers.secrets import router as secrets_router
from app.routers.discovery import router as discovery_router

__all__ = [
    "access_router", "credentials_router", "audit_router", 
    "analytics_router", "activity_router", "email_router", "contractor_router",
    "passkey_router", "device_router", "secrets_router", "discovery_router"
]




