"""
Contractor Vault - Device Schemas
Request/response models for device trust management
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeviceContext(BaseModel):
    """Device context captured from client."""
    fingerprint: Optional[str] = Field(None, description="Device fingerprint hash")
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_type: str = Field(default="desktop", description="desktop, mobile, or tablet")
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class DeviceInfoResponse(BaseModel):
    """Device info response."""
    id: str
    fingerprint: str
    contractor_email: str
    browser: Optional[str]
    os: Optional[str]
    device_type: str
    ip_address: Optional[str]
    country: Optional[str]
    city: Optional[str]
    is_trusted: bool
    is_blocked: bool
    trust_score: int
    first_seen: datetime
    last_seen: datetime
    access_count: int

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """List of devices."""
    devices: list[DeviceInfoResponse]
    total: int


class DeviceTrustRequest(BaseModel):
    """Request to update device trust status."""
    is_trusted: bool
    admin_email: str = Field(..., description="Admin making the change")
    reason: Optional[str] = None


class DeviceBlockRequest(BaseModel):
    """Request to block a device."""
    admin_email: str
    reason: str = Field(..., description="Reason for blocking")


class DeviceUnblockRequest(BaseModel):
    """Request to unblock a device."""
    admin_email: str


class DeviceValidationResult(BaseModel):
    """Result of device validation check."""
    is_allowed: bool
    device_id: Optional[str] = None
    trust_score: int
    is_new_device: bool
    is_blocked: bool
    warnings: list[str] = Field(default_factory=list)
    requires_additional_auth: bool = False
