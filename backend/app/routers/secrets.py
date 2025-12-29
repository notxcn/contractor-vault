"""
Contractor Vault - Secrets Router
API endpoints for secrets management
"""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models.secret import Secret, SecretType
from app.models.session_token import SessionToken, generate_secure_token
from app.services.encryption import EncryptionService, get_encryption_service
from app.schemas.secret import (
    SecretCreate,
    SecretUpdate,
    SecretRotate,
    SecretInfo,
    SecretListResponse,
    SecretShareRequest,
    SecretShareResponse,
    SecretClaimResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/secrets", tags=["Secrets Management"])


@router.post("", response_model=SecretInfo)
async def create_secret(
    payload: SecretCreate,
    request: Request,
    db: Session = Depends(get_db),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """Create a new secret."""
    admin_email = request.headers.get("X-Admin-Email", "admin@example.com")
    encrypted_value = encryption_service.encrypt(payload.value)
    
    secret = Secret(
        name=payload.name,
        secret_type=payload.secret_type.value,
        encrypted_value=encrypted_value,
        description=payload.description,
        secret_metadata=payload.metadata,
        tags=payload.tags,
        expires_at=payload.expires_at,
        rotation_reminder_days=payload.rotation_reminder_days,
        created_by=admin_email
    )
    
    db.add(secret)
    db.commit()
    db.refresh(secret)
    
    logger.info(f"Created secret '{payload.name}' by {admin_email}")
    
    return SecretInfo(
        id=secret.id,
        name=secret.name,
        secret_type=secret.secret_type,
        description=secret.description,
        secret_metadata=secret.secret_metadata,
        tags=secret.tags,
        is_active=secret.is_active,
        expires_at=secret.expires_at,
        needs_rotation=secret.needs_rotation(),
        created_by=secret.created_by,
        created_at=secret.created_at,
        updated_at=secret.updated_at,
        last_accessed_at=secret.last_accessed_at,
        access_count=secret.access_count
    )


@router.get("", response_model=SecretListResponse)
async def list_secrets(
    skip: int = 0,
    limit: int = 100,
    secret_type: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all secrets (without values)."""
    query = db.query(Secret)
    
    if active_only:
        query = query.filter(Secret.is_active == True)
    
    if secret_type:
        query = query.filter(Secret.secret_type == secret_type)
    
    secrets = query.order_by(Secret.created_at.desc()).offset(skip).limit(limit).all()
    
    return SecretListResponse(
        secrets=[
            SecretInfo(
                id=s.id,
                name=s.name,
                secret_type=s.secret_type,
                description=s.description,
                secret_metadata=s.secret_metadata,
                tags=s.tags,
                is_active=s.is_active,
                expires_at=s.expires_at,
                needs_rotation=s.needs_rotation(),
                created_by=s.created_by,
                created_at=s.created_at,
                updated_at=s.updated_at,
                last_accessed_at=s.last_accessed_at,
                access_count=s.access_count
            )
            for s in secrets
        ],
        total=len(secrets)
    )


@router.get("/{secret_id}", response_model=SecretInfo)
async def get_secret(
    secret_id: str,
    db: Session = Depends(get_db)
):
    """Get secret metadata (not the value)."""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    return SecretInfo(
        id=secret.id,
        name=secret.name,
        secret_type=secret.secret_type,
        description=secret.description,
        secret_metadata=secret.secret_metadata,
        tags=secret.tags,
        is_active=secret.is_active,
        expires_at=secret.expires_at,
        needs_rotation=secret.needs_rotation(),
        created_by=secret.created_by,
        created_at=secret.created_at,
        updated_at=secret.updated_at,
        last_accessed_at=secret.last_accessed_at,
        access_count=secret.access_count
    )


@router.patch("/{secret_id}", response_model=SecretInfo)
async def update_secret(
    secret_id: str,
    payload: SecretUpdate,
    db: Session = Depends(get_db)
):
    """Update secret metadata."""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    if payload.name is not None:
        secret.name = payload.name
    if payload.description is not None:
        secret.description = payload.description
    if payload.metadata is not None:
        secret.secret_metadata = payload.metadata
    if payload.tags is not None:
        secret.tags = payload.tags
    if payload.expires_at is not None:
        secret.expires_at = payload.expires_at
    if payload.rotation_reminder_days is not None:
        secret.rotation_reminder_days = payload.rotation_reminder_days
    if payload.is_active is not None:
        secret.is_active = payload.is_active
    
    db.commit()
    db.refresh(secret)
    
    return SecretInfo.model_validate(secret)


@router.post("/{secret_id}/rotate")
async def rotate_secret(
    secret_id: str,
    payload: SecretRotate,
    db: Session = Depends(get_db),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """Rotate a secret's value."""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    secret.encrypted_value = encryption_service.encrypt(payload.new_value)
    secret.last_rotated_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Rotated secret '{secret.name}'")
    return {"success": True, "message": "Secret rotated"}


@router.delete("/{secret_id}")
async def delete_secret(
    secret_id: str,
    db: Session = Depends(get_db)
):
    """Delete a secret."""
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    db.delete(secret)
    db.commit()
    
    logger.info(f"Deleted secret '{secret.name}'")
    return {"success": True, "message": "Secret deleted"}


@router.post("/share", response_model=SecretShareResponse)
async def share_secret(
    payload: SecretShareRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Generate a time-limited token to share a secret with a contractor."""
    secret = db.query(Secret).filter(Secret.id == payload.secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    if not secret.is_active:
        raise HTTPException(status_code=400, detail="Secret is not active")
    
    admin_email = request.headers.get("X-Admin-Email", "admin@example.com")
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)
    
    token = SessionToken(
        token=generate_secure_token(),
        credential_id=secret.id,
        contractor_email=payload.contractor_email,
        expires_at=expires_at,
        is_one_time=payload.max_uses == 1,
        allowed_ip=payload.allowed_ip,
        created_by=admin_email
    )
    
    db.add(token)
    db.commit()
    
    logger.info(f"Shared secret '{secret.name}' with {payload.contractor_email}")
    
    return SecretShareResponse(
        token=token.token,
        secret_name=secret.name,
        contractor_email=payload.contractor_email,
        expires_at=expires_at,
        max_uses=payload.max_uses
    )


@router.post("/claim/{token}", response_model=SecretClaimResponse)
async def claim_secret(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """Claim a shared secret using a token."""
    try:
        session_token = db.query(SessionToken).filter(
            SessionToken.token == token
        ).first()
        
        if not session_token:
            raise HTTPException(status_code=404, detail="Invalid token")
        
        # Check validity
        if not session_token.is_valid():
            raise HTTPException(status_code=410, detail="Token expired or revoked")
        
        # Capture Device Context
        device_header = request.headers.get("X-Device-Context")
        if device_header:
            try:
                import json
                from app.services.device_service import DeviceService
                from app.schemas.device import DeviceContext
                
                device_data = json.loads(device_header)
                context = DeviceContext(**device_data)
                
                # Register/Update device visibility
                device_service = DeviceService()
                device_service.get_or_create_device(
                    db=db,
                    contractor_email=session_token.contractor_email,
                    context=context,
                    ip_address=request.client.host
                )
            except Exception as e:
                logger.warning(f"Failed to capture device context: {e}")
                # Don't block claim on device capture failure
        
        secret = db.query(Secret).filter(Secret.id == session_token.credential_id).first()
        
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        decrypted_value = encryption_service.decrypt(secret.encrypted_value)
        
        session_token.use_count += 1
        session_token.last_used_at = datetime.now(timezone.utc)
        
        if session_token.is_one_time:
            session_token.is_revoked = True
            session_token.revoked_at = datetime.now(timezone.utc)
        
        secret.access_count += 1
        secret.last_accessed_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"Secret '{secret.name}' claimed by {session_token.contractor_email}")
        
        remaining = 0 if session_token.is_one_time else None
        
        return SecretClaimResponse(
            secret_name=secret.name,
            secret_type=secret.secret_type,
            value=decrypted_value,
            secret_metadata=secret.secret_metadata,
            expires_at=session_token.expires_at,
            remaining_uses=remaining
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming secret: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
