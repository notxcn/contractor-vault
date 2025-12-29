"""
Contractor Vault - Device Router
Device trust management and monitoring endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.device_service import get_device_service, DeviceService
from app.schemas.device import (
    DeviceContext,
    DeviceInfoResponse,
    DeviceListResponse,
    DeviceTrustRequest,
    DeviceBlockRequest,
    DeviceUnblockRequest,
    DeviceValidationResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["Device Trust"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("", response_model=DeviceListResponse)
async def list_all_devices(
    skip: int = 0,
    limit: int = 100,
    blocked_only: bool = False,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """List all devices."""
    devices = device_service.get_all_devices(db, skip, limit, blocked_only)
    return DeviceListResponse(
        devices=[DeviceInfoResponse.model_validate(d) for d in devices],
        total=len(devices)
    )


@router.get("/contractor/{contractor_email}", response_model=DeviceListResponse)
async def list_contractor_devices(
    contractor_email: str,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """List all devices for a specific contractor."""
    devices = device_service.get_devices_for_contractor(db, contractor_email)
    return DeviceListResponse(
        devices=[DeviceInfoResponse.model_validate(d) for d in devices],
        total=len(devices)
    )


@router.post("/validate", response_model=DeviceValidationResult)
async def validate_device(
    contractor_email: str,
    context: DeviceContext,
    request: Request,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Validate a device for access.
    
    Returns trust score and whether additional authentication is required.
    """
    ip_address = get_client_ip(request)
    
    result = device_service.validate_device(
        db=db,
        contractor_email=contractor_email,
        context=context,
        ip_address=ip_address
    )
    
    return result


@router.post("/{device_id}/trust")
async def trust_device(
    device_id: str,
    request: DeviceTrustRequest,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """Mark a device as trusted."""
    if request.is_trusted:
        success = device_service.trust_device(db, device_id, request.admin_email)
    else:
        # Untrust = reset to default state
        from app.models.device import DeviceInfo
        device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
        if device:
            device.is_trusted = False
            device.trust_score = 50
            db.commit()
            success = True
        else:
            success = False
    
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"success": True, "message": "Device trust updated"}


@router.post("/{device_id}/block")
async def block_device(
    device_id: str,
    request: DeviceBlockRequest,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """Block a device from accessing the system."""
    success = device_service.block_device(
        db=db,
        device_id=device_id,
        admin_email=request.admin_email,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"success": True, "message": "Device blocked"}


@router.post("/{device_id}/unblock")
async def unblock_device(
    device_id: str,
    request: DeviceUnblockRequest,
    db: Session = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """Unblock a device."""
    success = device_service.unblock_device(
        db=db,
        device_id=device_id,
        admin_email=request.admin_email
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"success": True, "message": "Device unblocked"}


@router.get("/{device_id}", response_model=DeviceInfoResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get device details."""
    from app.models.device import DeviceInfo
    device = db.query(DeviceInfo).filter(DeviceInfo.id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return DeviceInfoResponse.model_validate(device)
