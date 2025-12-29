"""
Contractor Vault - Passkey Schemas
Request/response models for WebAuthn passkey authentication
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Registration schemas
class PasskeyRegistrationBeginRequest(BaseModel):
    """Request to begin passkey registration."""
    contractor_email: str = Field(..., description="Email of contractor registering passkey")
    device_name: str = Field(default="My Device", description="Human-readable device name")


class PasskeyRegistrationBeginResponse(BaseModel):
    """Response with WebAuthn registration options."""
    challenge: str = Field(..., description="Base64url encoded challenge")
    rp_id: str = Field(..., description="Relying party ID")
    rp_name: str = Field(..., description="Relying party name")
    user_id: str = Field(..., description="User handle")
    user_name: str = Field(..., description="User display name")
    timeout: int = Field(default=60000, description="Timeout in milliseconds")
    attestation: str = Field(default="none", description="Attestation preference")
    authenticator_selection: dict = Field(default_factory=dict)


class PasskeyRegistrationCompleteRequest(BaseModel):
    """Request to complete passkey registration."""
    contractor_email: str
    challenge: str = Field(..., description="Original challenge")
    credential_id: str = Field(..., description="Base64url credential ID from authenticator")
    client_data_json: str = Field(..., description="Base64url client data")
    attestation_object: str = Field(..., description="Base64url attestation object")
    device_name: str = Field(default="My Device")


class PasskeyRegistrationCompleteResponse(BaseModel):
    """Response after successful registration."""
    success: bool
    credential_id: str
    device_name: str
    message: str


# Authentication schemas
class PasskeyAuthBeginRequest(BaseModel):
    """Request to begin passkey authentication."""
    contractor_email: str
    token_id: Optional[str] = Field(None, description="Token being claimed (if for session access)")


class PasskeyAuthBeginResponse(BaseModel):
    """Response with WebAuthn authentication options."""
    challenge: str
    rp_id: str
    timeout: int = 60000
    allowed_credentials: list[dict] = Field(default_factory=list)
    user_verification: str = "preferred"


class PasskeyAuthCompleteRequest(BaseModel):
    """Request to complete passkey authentication."""
    contractor_email: str
    challenge: str
    credential_id: str
    client_data_json: str
    authenticator_data: str
    signature: str
    user_handle: Optional[str] = None


class PasskeyAuthCompleteResponse(BaseModel):
    """Response after successful authentication."""
    success: bool
    contractor_email: str
    credential_id: str
    message: str


# Management schemas
class PasskeyCredentialInfo(BaseModel):
    """Info about a registered passkey."""
    id: str
    device_name: str
    credential_type: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class PasskeyListResponse(BaseModel):
    """List of passkeys for a contractor."""
    contractor_email: str
    passkeys: list[PasskeyCredentialInfo]
    count: int


class PasskeyDeleteRequest(BaseModel):
    """Request to delete a passkey."""
    credential_id: str
    contractor_email: str
