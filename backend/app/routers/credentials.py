"""
Contractor Vault - Credentials Router
CRUD operations for stored credentials
"""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Credential, AuditAction
from app.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialListResponse,
)
from app.services.encryption import get_encryption_service, EncryptionService
from app.services.audit_service import AuditService
from app.middleware.audit_middleware import get_audit_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Dependency for audit service."""
    return AuditService(db)


@router.post(
    "/",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new credential"
)
async def create_credential(
    request: Request,
    payload: CredentialCreate,
    db: Annotated[Session, Depends(get_db)],
    encryption_service: Annotated[EncryptionService, Depends(get_encryption_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Create a new stored credential.
    
    - Encrypts the password using Fernet
    - Logs CREDENTIAL_CREATED to audit trail
    """
    # Encrypt the password
    encrypted_password = encryption_service.encrypt(payload.password)
    
    # Create credential
    credential = Credential(
        name=payload.name,
        target_url=payload.target_url,
        username=payload.username,
        encrypted_password=encrypted_password,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    # Log creation
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=payload.created_by,
        action=AuditAction.CREDENTIAL_CREATED,
        target_resource=credential.target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "credential_id": credential.id,
            "credential_name": credential.name,
        },
        description=f"Created credential: {credential.name}"
    )
    
    logger.info(f"Credential created: {credential.name} by {payload.created_by}")
    
    return credential


@router.get(
    "/",
    response_model=CredentialListResponse,
    summary="List all credentials"
)
async def list_credentials(
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
):
    """
    List all stored credentials.
    
    - Returns paginated list
    - Passwords are never included in response
    """
    query = db.query(Credential)
    
    if active_only:
        query = query.filter(Credential.is_active == True)
    
    total = query.count()
    credentials = query.offset(skip).limit(limit).all()
    
    return CredentialListResponse(
        credentials=credentials,
        total=total
    )


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Get a specific credential"
)
async def get_credential(
    credential_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Get a specific credential by ID (password not included)."""
    credential = db.query(Credential).filter(
        Credential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    return credential


@router.patch(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Update a credential"
)
async def update_credential(
    request: Request,
    credential_id: str,
    payload: CredentialUpdate,
    admin_email: str,  # Would normally come from auth
    db: Annotated[Session, Depends(get_db)],
    encryption_service: Annotated[EncryptionService, Depends(get_encryption_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Update an existing credential.
    
    - Only provided fields are updated
    - If password is provided, it's re-encrypted
    - Logs CREDENTIAL_UPDATED to audit trail
    """
    credential = db.query(Credential).filter(
        Credential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle password encryption if provided
    if "password" in update_data:
        update_data["encrypted_password"] = encryption_service.encrypt(update_data.pop("password"))
    
    # Apply updates
    for field, value in update_data.items():
        setattr(credential, field, value)
    
    db.commit()
    db.refresh(credential)
    
    # Log update
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=admin_email,
        action=AuditAction.CREDENTIAL_UPDATED,
        target_resource=credential.target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "credential_id": credential.id,
            "updated_fields": list(update_data.keys()),
        },
        description=f"Updated credential: {credential.name}"
    )
    
    logger.info(f"Credential updated: {credential.name} by {admin_email}")
    
    return credential


@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a credential (soft delete)"
)
async def delete_credential(
    request: Request,
    credential_id: str,
    admin_email: str,  # Would normally come from auth
    db: Annotated[Session, Depends(get_db)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Soft delete a credential.
    
    - Marks as inactive rather than deleting
    - Logs CREDENTIAL_DELETED to audit trail
    """
    credential = db.query(Credential).filter(
        Credential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    credential.is_active = False
    db.commit()
    
    # Log deletion
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=admin_email,
        action=AuditAction.CREDENTIAL_DELETED,
        target_resource=credential.target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "credential_id": credential.id,
            "credential_name": credential.name,
        },
        description=f"Deleted credential: {credential.name}"
    )
    
    logger.info(f"Credential deleted: {credential.name} by {admin_email}")
    
    return None
