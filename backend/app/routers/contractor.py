"""
Contractor Router - Agency Bridge Feature
Authentication and multi-client management for contractors.
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.contractor_account import ContractorAccount, ClientLink

logger = logging.getLogger("contractor_vault.contractor")

router = APIRouter(prefix="/api/contractor", tags=["Contractor Portal"])


# ===== Schemas =====

class MagicLinkRequest(BaseModel):
    """Request for magic link login."""
    email: EmailStr


class MagicLinkVerify(BaseModel):
    """Verify magic link token."""
    email: EmailStr
    token: str


class ContractorProfile(BaseModel):
    """Contractor profile response."""
    id: str
    email: str
    display_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    linked_clients: list[dict]
    
    class Config:
        from_attributes = True


class ClientLinkResponse(BaseModel):
    """Client link details."""
    id: str
    client_name: str
    invited_by: Optional[str]
    linked_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Request to update contractor profile."""
    display_name: Optional[str] = None


# ===== Endpoints =====

@router.post("/auth/request-magic-link")
async def request_magic_link(
    payload: MagicLinkRequest,
    db: Session = Depends(get_db),
):
    """
    Request a magic link login email.
    
    Creates contractor account if doesn't exist.
    Sends email with login link (would integrate with email service).
    """
    # Find or create contractor account
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == payload.email
    ).first()
    
    if not contractor:
        contractor = ContractorAccount(email=payload.email)
        db.add(contractor)
    
    # Generate magic token
    token = secrets.token_urlsafe(32)
    contractor.magic_token = token
    contractor.magic_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    db.commit()
    
    # In production, would send email here
    # For demo, return the token directly
    logger.info(f"Magic link requested for {payload.email}")
    
    return {
        "success": True,
        "message": "Magic link sent to your email",
        # In production, remove this - only for testing
        "demo_token": token,
        "demo_link": f"contractor-vault://login?email={payload.email}&token={token}"
    }


@router.post("/auth/verify", response_model=ContractorProfile)
async def verify_magic_link(
    payload: MagicLinkVerify,
    db: Session = Depends(get_db),
):
    """
    Verify magic link token and log in.
    
    Returns contractor profile with linked clients.
    """
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == payload.email,
        ContractorAccount.magic_token == payload.token,
        ContractorAccount.is_active == True
    ).first()
    
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )
    
    # Check expiry
    if contractor.magic_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Magic link has expired"
        )
    
    # Clear token and update last login
    contractor.magic_token = None
    contractor.magic_token_expires = None
    contractor.last_login = datetime.now(timezone.utc)
    
    db.commit()
    
    # Get linked clients
    links = db.query(ClientLink).filter(
        ClientLink.contractor_id == contractor.id,
        ClientLink.is_active == True
    ).all()
    
    logger.info(f"Contractor {payload.email} logged in")
    
    return ContractorProfile(
        id=contractor.id,
        email=contractor.email,
        display_name=contractor.display_name,
        is_active=contractor.is_active,
        created_at=contractor.created_at,
        last_login=contractor.last_login,
        linked_clients=[
            {
                "id": link.id,
                "client_name": link.client_name,
                "linked_at": link.linked_at.isoformat()
            }
            for link in links
        ]
    )


@router.get("/profile/{email}", response_model=ContractorProfile)
async def get_contractor_profile(
    email: str,
    db: Session = Depends(get_db),
):
    """Get contractor profile and linked clients."""
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == email
    ).first()
    
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )
    
    links = db.query(ClientLink).filter(
        ClientLink.contractor_id == contractor.id,
        ClientLink.is_active == True
    ).all()
    
    return ContractorProfile(
        id=contractor.id,
        email=contractor.email,
        display_name=contractor.display_name,
        is_active=contractor.is_active,
        created_at=contractor.created_at,
        last_login=contractor.last_login,
        linked_clients=[
            {
                "id": link.id,
                "client_name": link.client_name,
                "linked_at": link.linked_at.isoformat()
            }
            for link in links
        ]
    )


@router.put("/profile/{email}")
async def update_contractor_profile(
    email: str,
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
):
    """Update contractor profile."""
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == email
    ).first()
    
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )
    
    if payload.display_name is not None:
        contractor.display_name = payload.display_name
    
    db.commit()
    
    return {"success": True, "message": "Profile updated"}


@router.get("/clients/{email}", response_model=list[ClientLinkResponse])
async def get_linked_clients(
    email: str,
    db: Session = Depends(get_db),
):
    """Get all clients linked to a contractor account."""
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == email
    ).first()
    
    if not contractor:
        return []
    
    links = db.query(ClientLink).filter(
        ClientLink.contractor_id == contractor.id
    ).all()
    
    return links


@router.post("/link")
async def link_client(
    contractor_email: str,
    client_name: str,
    invited_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Link a contractor to a client.
    
    Called by admin when inviting contractor.
    Creates contractor account if needed.
    """
    # Find or create contractor
    contractor = db.query(ContractorAccount).filter(
        ContractorAccount.email == contractor_email
    ).first()
    
    if not contractor:
        contractor = ContractorAccount(email=contractor_email)
        db.add(contractor)
        db.flush()
    
    # Check if already linked
    existing = db.query(ClientLink).filter(
        ClientLink.contractor_id == contractor.id,
        ClientLink.client_name == client_name
    ).first()
    
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            return {"success": True, "message": "Client link reactivated", "link_id": existing.id}
        return {"success": True, "message": "Already linked", "link_id": existing.id}
    
    # Create link
    link = ClientLink(
        contractor_id=contractor.id,
        client_name=client_name,
        invited_by=invited_by,
    )
    db.add(link)
    db.commit()
    
    logger.info(f"Linked {contractor_email} to client {client_name}")
    
    return {"success": True, "message": "Client linked", "link_id": link.id}


@router.delete("/unlink/{link_id}")
async def unlink_client(
    link_id: str,
    db: Session = Depends(get_db),
):
    """Unlink a contractor from a client."""
    link = db.query(ClientLink).filter(ClientLink.id == link_id).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    link.is_active = False
    db.commit()
    
    return {"success": True, "message": "Client unlinked"}
