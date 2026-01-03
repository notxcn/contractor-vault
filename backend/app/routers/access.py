"""
Contractor Vault - Access Router
Token generation, claiming, and revocation endpoints
"""
import base64
import logging
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Credential, SessionToken, AuditLog, AuditAction
from app.schemas.session_token import (
    GenerateTokenRequest,
    GenerateTokenResponse,
    ClaimTokenRequest,
    ClaimTokenResponse,
    RevokeTokenRequest,
    RevokeAllRequest,
    RevokeResponse,
    TokenListItem,
)
from app.services.encryption import get_encryption_service, EncryptionService
from app.services.token_service import get_token_service, TokenService
from app.services.audit_service import AuditService
from app.services.discord_webhook import get_discord_service
from app.middleware.audit_middleware import get_audit_context
from app.routers.auth import require_auth
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/access", tags=["Access Control"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Dependency for audit service."""
    return AuditService(db)


@router.get(
    "/tokens",
    response_model=list[TokenListItem],
    summary="List access tokens created by the current user"
)
async def list_tokens(
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(require_auth),
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    List session tokens created by the current authenticated user.
    
    Args:
        status_filter: Optional filter - 'active', 'expired', 'revoked', or None for all
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of tokens created by the current user
    """
    # Filter by current user's email - users only see their own tokens
    # UNLESS they are a superuser
    if current_user.is_superuser:
        query = db.query(SessionToken)
    else:
        query = db.query(SessionToken).filter(
            SessionToken.created_by == current_user.email
        )
    
    now = datetime.now(timezone.utc)
    
    if status_filter == "active":
        query = query.filter(
            SessionToken.is_revoked == False,
            SessionToken.expires_at > now
        )
    elif status_filter == "expired":
        query = query.filter(
            SessionToken.is_revoked == False,
            SessionToken.expires_at <= now
        )
    elif status_filter == "revoked":
        query = query.filter(SessionToken.is_revoked == True)
    
    tokens = query.order_by(SessionToken.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for token in tokens:
        # Determine status
        # Handle potentially naive token.expires_at
        token_expires = token.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)
        
        if token.is_revoked:
            status = "revoked"
        elif token_expires <= now:
            status = "expired"
        else:
            status = "active"
        
        # Get credential info if available
        credential = db.query(Credential).filter(Credential.id == token.credential_id).first()
        
        result.append(TokenListItem(
            id=token.id,
            token=token.token[:8] + "...",  # Truncate for security
            credential_id=token.credential_id,
            credential_name=credential.name if credential else None,
            target_url=credential.target_url if credential else None,
            contractor_email=token.contractor_email,
            expires_at=token.expires_at,
            is_revoked=token.is_revoked,
            revoked_at=token.revoked_at,
            revoked_by=token.revoked_by,
            created_at=token.created_at,
            created_by=token.created_by,
            use_count=token.use_count,
            status=status,
        ))
    
    return result


@router.post(
    "/generate-access-token",
    response_model=GenerateTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a time-bombed access token for a contractor"
)
async def generate_access_token(
    request: Request,
    payload: GenerateTokenRequest,
    db: Annotated[Session, Depends(get_db)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Generate a temporary access token for a contractor.
    
    - Validates the credential exists
    - Creates a session token with expiry
    - Generates a signed JWT
    - Logs GRANT_ACCESS to audit trail
    """
    # Verify credential exists and is active
    credential = db.query(Credential).filter(
        Credential.id == payload.credential_id,
        Credential.is_active == True
    ).first()
    
    if not credential:
        logger.warning(f"Token generation failed: Credential {payload.credential_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found or inactive"
        )
    
    # Calculate expiry
    expires_at = token_service.calculate_expiry(payload.duration_minutes)
    
    # Create session token
    session_token = SessionToken(
        credential_id=credential.id,
        contractor_email=payload.contractor_email,
        expires_at=expires_at,
        created_by=payload.admin_email,
        allowed_ip=payload.allowed_ip,
    )
    db.add(session_token)
    db.commit()
    db.refresh(session_token)
    
    # Generate JWT
    jwt_token = token_service.create_access_jwt(
        token_id=session_token.id,
        credential_id=credential.id,
        contractor_email=payload.contractor_email,
        expires_at=expires_at,
        allowed_ip=payload.allowed_ip,
    )
    
    # Log to audit trail
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=payload.admin_email,
        action=AuditAction.GRANT_ACCESS,
        target_resource=credential.target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "credential_id": credential.id,
            "contractor_email": payload.contractor_email,
            "duration_minutes": payload.duration_minutes,
            "user_agent": audit_context["user_agent"],
            "notes": payload.notes,
        },
        description=f"Granted {payload.duration_minutes}min access to {credential.name} for {payload.contractor_email}"
    )
    
    claim_url = f"https://app.contractorvault.com/claim/{session_token.token}"
    
    logger.info(
        f"Generated access token for {payload.contractor_email} "
        f"to {credential.name}, expires at {expires_at.isoformat()}"
    )
    
    # Send Discord notification
    discord = get_discord_service()
    await discord.notify_access_granted(
        contractor_email=payload.contractor_email,
        credential_name=credential.name,
        duration_minutes=payload.duration_minutes,
        admin_email=payload.admin_email,
    )
    
    admin_dashboard_url = "https://contractor-vault-production.up.railway.app/dashboard"
    
    return GenerateTokenResponse(
        token_id=session_token.id,
        claim_url=claim_url,
        access_token=jwt_token,
        expires_at=expires_at,
        contractor_email=payload.contractor_email,
        credential_name=credential.name,
        admin_dashboard_url=admin_dashboard_url,
    )


@router.post(
    "/claim/{token}",
    response_model=ClaimTokenResponse,
    summary="Claim an access token and receive encrypted credentials"
)
async def claim_token(
    request: Request,
    token: str,
    db: Annotated[Session, Depends(get_db)],
    encryption_service: Annotated[EncryptionService, Depends(get_encryption_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Claim an access token and receive encrypted credential payload.
    
    - Validates token exists and is not expired/revoked
    - Returns encrypted password for client-side decryption
    - Logs INJECTION_SUCCESS to audit trail
    """
    # Find the session token
    session_token = db.query(SessionToken).filter(
        SessionToken.token == token
    ).first()
    
    if not session_token:
        logger.warning(f"Token claim failed: Token not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Check token validity
    if not session_token.is_valid():
        if session_token.is_revoked:
            logger.warning(f"Token claim failed: Token revoked")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has been revoked"
            )
        else:
            # Log expiration
            audit_context = get_audit_context(request)
            audit_service.log(
                actor=session_token.contractor_email,
                action=AuditAction.SESSION_EXPIRED,
                target_resource=session_token.credential.target_url,
                ip_address=audit_context["client_ip"],
                extra_data={"token_id": session_token.id},
                description=f"Attempted to use expired token"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has expired"
            )

    # IP Whitelist Validation
    if session_token.allowed_ip:
        audit_context = get_audit_context(request)
        client_ip = audit_context["client_ip"]
        
        if client_ip != session_token.allowed_ip and client_ip != "unknown":
            logger.warning(f"IP mismatch for token {session_token.id}. Expected {session_token.allowed_ip}, got {client_ip}")
            audit_service.log(
                actor=session_token.contractor_email,
                action=AuditAction.SECURITY_ALERT,
                target_resource=session_token.credential.target_url,
                ip_address=client_ip,
                extra_data={"expected_ip": session_token.allowed_ip, "token_id": session_token.id},
                description=f"Blocked access from unauthorized IP {client_ip} (Allowed: {session_token.allowed_ip})"
            )
            # Send Discord alert
            try:
                discord = get_discord_service()
                await discord.notify_security_alert(
                   alert_type="IP Whitelist Mismatch",
                   details=f"User {session_token.contractor_email} attempted access from {client_ip} (Allowed: {session_token.allowed_ip})"
                )
            except Exception:
                pass # Don't block on discord error

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP address"
            )
    
    credential = session_token.credential
    
    # Update usage tracking
    session_token.last_used_at = datetime.now(timezone.utc)
    session_token.use_count += 1
    db.commit()
    
    # Log successful injection
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=session_token.contractor_email,
        action=AuditAction.INJECTION_SUCCESS,
        target_resource=credential.target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "token_id": session_token.id,
            "use_count": session_token.use_count,
            "user_agent": audit_context["user_agent"],
        },
        description=f"Credential injected for {credential.name}"
    )
    
    # Return encrypted password (base64 encoded for JSON transport)
    encrypted_password_b64 = base64.b64encode(credential.encrypted_password).decode("utf-8")
    
    logger.info(
        f"Token claimed: {session_token.contractor_email} accessed {credential.name} "
        f"(use #{session_token.use_count})"
    )
    
    # Send Discord notification (only on first use)
    if session_token.use_count == 1:
        discord = get_discord_service()
        await discord.notify_access_claimed(
            contractor_email=session_token.contractor_email,
            credential_name=credential.name,
            ip_address=audit_context["client_ip"],
        )
    
    return ClaimTokenResponse(
        success=True,
        credential_name=credential.name,
        target_url=credential.target_url,
        username=credential.username,
        encrypted_password=encrypted_password_b64,
        expires_at=session_token.expires_at,
    )


@router.get(
    "/validate/{token}",
    summary="Check if a token is still valid (for extension polling)"
)
async def validate_token(
    token: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Lightweight endpoint for the extension to poll status.
    Returns { valid: bool, status: str }
    """
    token_obj = db.query(SessionToken).filter(SessionToken.token == token).first()
    
    if not token_obj:
        return {"valid": False, "status": "not_found"}
        
    if token_obj.is_revoked:
        return {"valid": False, "status": "revoked"}
        
    now = datetime.now(timezone.utc)
    if token_obj.expires_at <= now:
        return {"valid": False, "status": "expired"}
        
    return {"valid": True, "status": "active"}


@router.post(
    "/revoke/{token_id}",
    response_model=RevokeResponse,
    summary="Revoke a specific access token"
)
async def revoke_token(
    request: Request,
    token_id: str,
    payload: RevokeTokenRequest,
    db: Annotated[Session, Depends(get_db)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    Revoke a specific session token.
    
    - Marks token as revoked
    - Logs REVOKE_ACCESS to audit trail
    """
    session_token = db.query(SessionToken).filter(
        SessionToken.id == token_id
    ).first()
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    if session_token.is_revoked:
        return RevokeResponse(
            success=True,
            revoked_count=0,
            message="Token was already revoked"
        )
    
    # Revoke the token
    session_token.is_revoked = True
    session_token.revoked_at = datetime.now(timezone.utc)
    session_token.revoked_by = payload.admin_email
    db.commit()
    
    # Get resource info (handle both Credential and StoredSession tokens)
    credential = db.query(Credential).filter(Credential.id == session_token.credential_id).first()
    credential_name = credential.name if credential else "Session"
    target_url = credential.target_url if credential else f"session:{session_token.credential_id}"
    
    # Log revocation
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=payload.admin_email,
        action=AuditAction.REVOKE_ACCESS,
        target_resource=target_url,
        ip_address=audit_context["client_ip"],
        extra_data={
            "token_id": session_token.id,
            "contractor_email": session_token.contractor_email,
            "reason": payload.reason,
        },
        description=f"Revoked access for {session_token.contractor_email} to {credential_name}"
    )
    
    logger.warning(
        f"Token revoked: {token_id} for {session_token.contractor_email} "
        f"by {payload.admin_email}"
    )
    
    # Send Discord notification
    try:
        discord = get_discord_service()
        await discord.notify_access_revoked(
            contractor_email=session_token.contractor_email,
            credential_name=credential_name,
            admin_email=payload.admin_email,
            reason=payload.reason,
        )
    except Exception as e:
        logger.error(f"Failed to send discord notification: {e}")
    
    return RevokeResponse(
        success=True,
        revoked_count=1,
        message=f"Successfully revoked token for {session_token.contractor_email}"
    )


@router.post(
    "/revoke-all/{contractor_email}",
    response_model=RevokeResponse,
    summary="Revoke ALL active tokens for a contractor (Kill Switch)"
)
async def revoke_all_tokens(
    request: Request,
    contractor_email: str,
    payload: RevokeAllRequest,
    db: Annotated[Session, Depends(get_db)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    """
    KILL SWITCH: Revoke all active tokens for a contractor.
    
    - Finds all non-revoked, non-expired tokens for the contractor
    - Marks all as revoked
    - Logs high-priority REVOKE_ACCESS entry
    
    Use this when a contractor's access needs to be immediately terminated.
    """
    now = datetime.now(timezone.utc)
    
    # Find all active tokens for this contractor
    active_tokens = db.query(SessionToken).filter(
        SessionToken.contractor_email == contractor_email,
        SessionToken.is_revoked == False,
        SessionToken.expires_at > now
    ).all()
    
    if not active_tokens:
        return RevokeResponse(
            success=True,
            revoked_count=0,
            message=f"No active tokens found for {contractor_email}"
        )
    
    # Revoke all tokens
    revoked_credentials = set()
    for token in active_tokens:
        token.is_revoked = True
        token.revoked_at = now
        token.revoked_by = payload.admin_email
        revoked_credentials.add(token.credential.target_url)
    
    db.commit()
    
    # Log high-priority revocation (KILL SWITCH)
    audit_context = get_audit_context(request)
    audit_service.log(
        actor=payload.admin_email,
        action=AuditAction.REVOKE_ACCESS,
        target_resource=f"KILL_SWITCH:{contractor_email}",
        ip_address=audit_context["client_ip"],
        extra_data={
            "contractor_email": contractor_email,
            "revoked_count": len(active_tokens),
            "affected_resources": list(revoked_credentials),
            "reason": payload.reason,
            "priority": "HIGH",
        },
        description=f"KILL SWITCH: Revoked ALL {len(active_tokens)} tokens for {contractor_email}"
    )
    
    logger.warning(
        f"KILL SWITCH activated: Revoked {len(active_tokens)} tokens "
        f"for {contractor_email} by {payload.admin_email}"
    )
    
    # Send Discord notification
    discord = get_discord_service()
    await discord.notify_kill_switch(
        contractor_email=contractor_email,
        revoked_count=len(active_tokens),
        admin_email=payload.admin_email,
        reason=payload.reason,
    )
    
    return RevokeResponse(
        success=True,
        revoked_count=len(active_tokens),
        message=f"Kill switch activated: Revoked {len(active_tokens)} tokens for {contractor_email}"
    )
