"""
Session/Cookie schemas for Contractor Vault
Allows sharing authenticated sessions instead of passwords
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class CookieData(BaseModel):
    """Single cookie data structure - flexible to accept various formats."""
    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False
    httpOnly: bool = False
    sameSite: str = "lax"
    expirationDate: Optional[float] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from Chrome cookies API


class SessionCreate(BaseModel):
    """Request to store an authenticated session."""
    name: str = Field(..., description="Friendly name for this session")
    target_url: str = Field(..., description="Target site URL")
    cookies: List[CookieData] = Field(..., description="List of cookies to store")
    created_by: str = Field(..., description="Admin email")
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    """Response after creating a session."""
    id: str
    name: str
    target_url: str
    cookie_count: int
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionClaimResponse(BaseModel):
    """Response when claiming a session token."""
    success: bool
    session_name: str
    target_url: str
    cookies: List[dict]  # Return as raw dicts to avoid validation issues
    expires_at: datetime
    message: str
