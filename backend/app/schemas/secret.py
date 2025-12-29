"""
Contractor Vault - Secret Schemas
Request/response models for secrets management
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class SecretTypeEnum(str, Enum):
    """Types of secrets."""
    API_KEY = "api_key"
    DATABASE = "database"
    SSH_KEY = "ssh_key"
    ENV_VAR = "env_var"
    OAUTH_TOKEN = "oauth_token"
    CERTIFICATE = "certificate"
    OTHER = "other"


class SecretCreate(BaseModel):
    """Request to create a new secret."""
    name: str = Field(..., min_length=1, max_length=255)
    secret_type: SecretTypeEnum = SecretTypeEnum.OTHER
    value: str = Field(..., min_length=1, description="The secret value (will be encrypted)")
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    expires_at: Optional[datetime] = None
    rotation_reminder_days: Optional[int] = None


class SecretUpdate(BaseModel):
    """Request to update a secret."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    expires_at: Optional[datetime] = None
    rotation_reminder_days: Optional[int] = None
    is_active: Optional[bool] = None


class SecretRotate(BaseModel):
    """Request to rotate a secret value."""
    new_value: str = Field(..., min_length=1, description="New secret value")


class SecretInfo(BaseModel):
    """Secret info (without the actual value)."""
    id: str
    name: str
    secret_type: str
    description: Optional[str]
    secret_metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]]
    is_active: bool
    expires_at: Optional[datetime]
    needs_rotation: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime]
    access_count: int

    class Config:
        from_attributes = True


class SecretListResponse(BaseModel):
    """List of secrets."""
    secrets: list[SecretInfo]
    total: int


class SecretShareRequest(BaseModel):
    """Request to share a secret with a contractor."""
    secret_id: str
    contractor_email: str
    duration_minutes: int = Field(default=60, ge=1, le=10080)  # Max 1 week
    max_uses: Optional[int] = Field(None, ge=1)
    require_passkey: bool = False
    allowed_ip: Optional[str] = None
    note: Optional[str] = None


class SecretShareResponse(BaseModel):
    """Response with access token for shared secret."""
    token: str
    secret_name: str
    contractor_email: str
    expires_at: datetime
    max_uses: Optional[int]


class SecretClaimResponse(BaseModel):
    """Response when claiming a shared secret."""
    secret_name: str
    secret_type: str
    value: str = Field(..., description="The decrypted secret value")
    secret_metadata: Optional[dict[str, Any]] = None
    expires_at: datetime
    remaining_uses: Optional[int]
