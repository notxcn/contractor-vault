"""
Contractor Vault - Credential Schemas
Pydantic models for credential API validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl


class CredentialBase(BaseModel):
    """Base schema for credential data."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Friendly name for the credential",
        examples=["AWS Console", "GitHub Admin"]
    )
    target_url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL where credential is used",
        examples=["https://aws.amazon.com/console"]
    )
    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Username or email for the credential",
        examples=["admin@company.com"]
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes about the credential"
    )


class CredentialCreate(CredentialBase):
    """Schema for creating a new credential."""
    password: str = Field(
        ...,
        min_length=1,
        description="Password to encrypt and store (never returned in responses)"
    )
    created_by: EmailStr = Field(
        ...,
        description="Email of admin creating this credential"
    )


class CredentialUpdate(BaseModel):
    """Schema for updating an existing credential."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_url: Optional[str] = Field(None, min_length=1, max_length=2048)
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = Field(None, max_length=1000)


class CredentialResponse(BaseModel):
    """Schema for credential API responses (password never included)."""
    id: str
    name: str
    target_url: str
    username: str
    notes: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class CredentialListResponse(BaseModel):
    """Schema for listing credentials."""
    credentials: list[CredentialResponse]
    total: int
