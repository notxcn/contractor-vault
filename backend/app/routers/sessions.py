"""
Session router for storing and sharing authenticated browser sessions.
"""
import json
import base64
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stored_session import StoredSession
from app.models import SessionToken, AuditLog, AuditAction
from app.services import EncryptionService, AuditService, TokenService
from app.schemas.session import (
    SessionCreate, 
    SessionResponse, 
    SessionClaimResponse,
    CookieData
)
from app.schemas.session_token import GenerateTokenRequest, GenerateTokenResponse

logger = logging.getLogger("contractor_vault.sessions")
router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

# Services
encryption_service = EncryptionService()
token_service = TokenService()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def store_session(
    session_data: SessionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Store an authenticated browser session (cookies) for sharing.
    
    The admin captures cookies from their authenticated browser and
    stores them encrypted in the vault.
    """
    # Parse domain from URL
    parsed_url = urlparse(session_data.target_url)
    target_domain = parsed_url.netloc or parsed_url.path.split('/')[0]
    
    # Serialize and encrypt cookies
    cookies_json = json.dumps([cookie.model_dump() for cookie in session_data.cookies])
    encrypted_cookies = encryption_service.encrypt(cookies_json)
    
    # Store as base64 for text column
    encrypted_b64 = base64.b64encode(encrypted_cookies).decode()
    
    # Create session record
    stored_session = StoredSession(
        name=session_data.name,
        target_url=session_data.target_url,
        target_domain=target_domain,
        encrypted_cookies=encrypted_b64.encode(),
        cookie_count=len(session_data.cookies),
        notes=session_data.notes,
        created_by=session_data.created_by,
    )
    
    db.add(stored_session)
    db.commit()
    db.refresh(stored_session)
    
    # Audit log
    audit_service = AuditService(db)
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    
    audit_service.log(
        actor=session_data.created_by,
        action=AuditAction.CREDENTIAL_CREATED,
        target_resource=session_data.target_url,
        ip_address=ip_address.split(",")[0].strip() if ip_address else "unknown",
        extra_data={
            "type": "session",
            "session_id": stored_session.id,
            "cookie_count": stored_session.cookie_count,
            "domain": target_domain,
        },
        description=f"Stored authenticated session for {target_domain} ({stored_session.cookie_count} cookies)"
    )
    
    return SessionResponse(
        id=stored_session.id,
        name=stored_session.name,
        target_url=stored_session.target_url,
        cookie_count=stored_session.cookie_count,
        created_by=stored_session.created_by,
        created_at=stored_session.created_at,
    )


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all stored sessions (without cookie data)."""
    sessions = db.query(StoredSession).filter(
        StoredSession.is_active == True
    ).offset(skip).limit(limit).all()
    
    return [
        SessionResponse(
            id=s.id,
            name=s.name,
            target_url=s.target_url,
            cookie_count=s.cookie_count,
            created_by=s.created_by,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post("/generate-token", response_model=GenerateTokenResponse)
async def generate_session_token(
    token_request: GenerateTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a time-limited access token for a stored session.
    This is like generate-access-token but for session sharing.
    """
    # Find the session (credential_id is actually session_id here)
    stored_session = db.query(StoredSession).filter(
        StoredSession.id == token_request.credential_id,
        StoredSession.is_active == True
    ).first()
    
    if not stored_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Calculate expiry
    expires_at = token_service.calculate_expiry(token_request.duration_minutes)
    
    # Create session token
    session_token = SessionToken(
        credential_id=stored_session.id,
        contractor_email=token_request.contractor_email,
        expires_at=expires_at,
        created_by=token_request.admin_email,
    )
    
    db.add(session_token)
    db.commit()
    db.refresh(session_token)
    
    # Generate JWT
    access_jwt = token_service.create_access_jwt(
        token_id=session_token.id,
        credential_id=stored_session.id,
        contractor_email=token_request.contractor_email,
        expires_at=expires_at,
    )
    
    # Build claim URL
    claim_url = f"https://app.contractorvault.com/claim/{session_token.token}"
    
    # Audit log
    audit_service = AuditService(db)
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    
    audit_service.log(
        actor=token_request.admin_email,
        action=AuditAction.GRANT_ACCESS,
        target_resource=stored_session.target_url,
        ip_address=ip_address.split(",")[0].strip() if ip_address else "unknown",
        extra_data={
            "type": "session",
            "session_id": stored_session.id,
            "token_id": session_token.id,
            "contractor": token_request.contractor_email,
            "duration_minutes": token_request.duration_minutes,
        },
        description=f"Granted session access to {token_request.contractor_email} for {stored_session.name}"
    )
    
    return GenerateTokenResponse(
        token_id=session_token.id,
        claim_url=claim_url,
        access_token=access_jwt,
        expires_at=expires_at,
        credential_name=stored_session.name,
        target_url=stored_session.target_url,
    )


@router.post("/claim/{token}")
async def claim_session(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Claim a session token and retrieve the cookies for injection.
    This returns the decrypted cookies so the extension can inject them.
    """
    import traceback
    try:
        # Find the token
        session_token = db.query(SessionToken).filter(
            SessionToken.token == token
        ).first()
        
        if not session_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        # Check if expired (handle timezone-naive timestamps)
        expires_at = session_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Token has expired"
            )
        
        # Check if revoked
        if session_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has been revoked"
            )
        
        # Find the stored session
        stored_session = db.query(StoredSession).filter(
            StoredSession.id == session_token.credential_id,
            StoredSession.is_active == True
        ).first()
        
        if not stored_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Decrypt cookies
        encrypted_b64 = stored_session.encrypted_cookies
        if isinstance(encrypted_b64, bytes):
            encrypted_b64 = encrypted_b64.decode()
        
        encrypted_cookies = base64.b64decode(encrypted_b64)
        cookies_json = encryption_service.decrypt(encrypted_cookies)
        cookies_data = json.loads(cookies_json)
        
        # Update token usage
        session_token.use_count += 1
        session_token.last_used_at = datetime.now(timezone.utc)
        db.commit()
        
        # Audit log
        audit_service = AuditService(db)
        ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        
        audit_service.log(
            actor=session_token.contractor_email,
            action=AuditAction.INJECTION_SUCCESS,
            target_resource=stored_session.target_url,
            ip_address=ip_address.split(",")[0].strip() if ip_address else "unknown",
            extra_data={
                "type": "session",
                "session_id": stored_session.id,
                "token_id": session_token.id,
                "cookie_count": len(cookies_data),
            },
            description=f"Session claimed for {stored_session.name}"
        )
        
        # Ensure expires_at has timezone info for proper JS parsing
        expires_at = session_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # Return cookies for injection
        return {
            "success": True,
            "session_name": stored_session.name,
            "target_url": stored_session.target_url,
            "cookies": cookies_data,
            "expires_at": expires_at.isoformat(),
            "message": f"Session ready for injection ({len(cookies_data)} cookies)"
        }
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

