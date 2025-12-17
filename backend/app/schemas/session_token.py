"""
Contractor Vault - Session Token Schemas
Pydantic models for token generation and claim API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class GenerateTokenRequest(BaseModel):
    """Schema for generating a new access token."""
    credential_id: str = Field(
        ...,
        description="UUID of the credential to grant access to"
    )
    contractor_email: str = Field(
        ...,
        description="Email of the contractor receiving access"
    )
    duration_minutes: int = Field(
        60,
        gt=0,
        le=1440,  # Max 24 hours
        description="Token validity duration in minutes (default: 60, max: 1440)"
    )
    admin_email: str = Field(
        ...,
        description="Email of admin granting access"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes about why access was granted"
    )


class GenerateTokenResponse(BaseModel):
    """Response after generating an access token."""
    token_id: str = Field(
        ...,
        description="Internal token ID for tracking"
    )
    claim_url: str = Field(
        ...,
        description="URL for contractor to claim access",
        examples=["https://app.contractorvault.com/claim/abc123xyz"]
    )
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    expires_at: datetime = Field(
        ...,
        description="Token expiration timestamp (UTC)"
    )
    contractor_email: str = Field(
        ...,
        description="Email of contractor receiving access"
    )
    credential_name: str
    admin_dashboard_url: str = Field(
        ...,
        description="URL to the admin dashboard for managing this session"
    )


class ClaimTokenRequest(BaseModel):
    """Schema for claiming an access token."""
    token: str = Field(
        ...,
        description="The token string from the claim URL"
    )


class ClaimTokenResponse(BaseModel):
    """
    Response when contractor claims a token.
    Contains encrypted credential payload.
    """
    success: bool
    credential_name: str = Field(
        ...,
        description="Name of the credential being accessed"
    )
    target_url: str = Field(
        ...,
        description="URL where credential should be used"
    )
    username: str = Field(
        ...,
        description="Username for the credential"
    )
    encrypted_password: str = Field(
        ...,
        description="Base64-encoded encrypted password (client decrypts)"
    )
    expires_at: datetime = Field(
        ...,
        description="When this access expires"
    )


class RevokeTokenRequest(BaseModel):
    """Schema for revoking a specific token."""
    token_id: str = Field(
        ...,
        description="ID of the token to revoke"
    )
    admin_email: EmailStr = Field(
        ...,
        description="Email of admin revoking access"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for revocation"
    )


class RevokeAllRequest(BaseModel):
    """Schema for revoking all tokens for a contractor."""
    contractor_email: EmailStr = Field(
        ...,
        description="Email of contractor whose tokens to revoke"
    )
    admin_email: EmailStr = Field(
        ...,
        description="Email of admin revoking access"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for bulk revocation"
    )


class RevokeResponse(BaseModel):
    """Response after revoking tokens."""
    success: bool
    revoked_count: int = Field(
        ...,
        description="Number of tokens revoked"
    )
    message: str


class TokenListItem(BaseModel):
    """Schema for displaying a token in the admin dashboard."""
    id: str
    token: str
    credential_id: str
    credential_name: Optional[str] = None
    target_url: Optional[str] = None
    contractor_email: str
    expires_at: datetime
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    created_at: datetime
    created_by: str
    use_count: int
    status: str = Field(
        ...,
        description="Token status: 'active', 'expired', or 'revoked'"
    )
    
    class Config:
        from_attributes = True
