"""
Contractor Vault - FastAPI Dependencies
Reusable dependency injection utilities
"""
from typing import Annotated
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.encryption import get_encryption_service, EncryptionService
from app.services.token_service import get_token_service, TokenService
from app.services.audit_service import AuditService


def get_audit_service(db: Annotated[Session, Depends(get_db)]) -> AuditService:
    """Provide audit service with database session."""
    return AuditService(db)


# Type aliases for cleaner route signatures
DBSession = Annotated[Session, Depends(get_db)]
EncryptionDep = Annotated[EncryptionService, Depends(get_encryption_service)]
TokenDep = Annotated[TokenService, Depends(get_token_service)]
AuditDep = Annotated[AuditService, Depends(get_audit_service)]


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, handling proxies.
    
    Priority:
    1. X-Forwarded-For (first IP)
    2. X-Real-IP
    3. Direct client IP
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    if request.client:
        return request.client.host
    
    return "unknown"
