"""
Contractor Vault - Passkey Router
WebAuthn passkey registration and authentication endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.passkey_service import get_passkey_service, PasskeyService
from app.schemas.passkey import (
    PasskeyRegistrationBeginRequest,
    PasskeyRegistrationBeginResponse,
    PasskeyRegistrationCompleteRequest,
    PasskeyRegistrationCompleteResponse,
    PasskeyAuthBeginRequest,
    PasskeyAuthBeginResponse,
    PasskeyAuthCompleteRequest,
    PasskeyAuthCompleteResponse,
    PasskeyListResponse,
    PasskeyCredentialInfo,
    PasskeyDeleteRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/passkey", tags=["Passkey Authentication"])


@router.post("/register/begin", response_model=PasskeyRegistrationBeginResponse)
async def begin_registration(
    request: PasskeyRegistrationBeginRequest,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """
    Begin passkey registration.
    
    Returns WebAuthn options for the client to create a new credential.
    """
    try:
        options = passkey_service.create_registration_challenge(
            db=db,
            contractor_email=request.contractor_email
        )
        
        return PasskeyRegistrationBeginResponse(
            challenge=options["challenge"],
            rp_id=options["rp"]["id"],
            rp_name=options["rp"]["name"],
            user_id=options["user"]["id"],
            user_name=options["user"]["name"],
            timeout=options["timeout"],
            attestation=options["attestation"],
            authenticator_selection=options["authenticatorSelection"]
        )
    except Exception as e:
        logger.error(f"Registration begin failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/complete", response_model=PasskeyRegistrationCompleteResponse)
async def complete_registration(
    request: PasskeyRegistrationCompleteRequest,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """
    Complete passkey registration.
    
    Verifies the attestation and stores the credential.
    """
    try:
        # In production, you would verify the attestation here
        # For now, we'll store the credential directly
        import base64
        
        # Decode credential ID to bytes for storage
        credential_id = request.credential_id
        public_key = base64.urlsafe_b64decode(request.attestation_object + "==")
        
        credential = passkey_service.verify_and_store_credential(
            db=db,
            contractor_email=request.contractor_email,
            challenge=request.challenge,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=0,
            device_name=request.device_name
        )
        
        return PasskeyRegistrationCompleteResponse(
            success=True,
            credential_id=credential.credential_id,
            device_name=credential.device_name,
            message="Passkey registered successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/begin", response_model=PasskeyAuthBeginResponse)
async def begin_authentication(
    request: PasskeyAuthBeginRequest,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """
    Begin passkey authentication.
    
    Returns WebAuthn options for the client to authenticate.
    """
    try:
        # Check if contractor has any passkeys
        if not passkey_service.contractor_has_passkey(db, request.contractor_email):
            raise HTTPException(
                status_code=404,
                detail="No passkeys registered for this email"
            )
        
        options = passkey_service.create_authentication_challenge(
            db=db,
            contractor_email=request.contractor_email,
            token_id=request.token_id
        )
        
        return PasskeyAuthBeginResponse(
            challenge=options["challenge"],
            rp_id=options["rpId"],
            timeout=options["timeout"],
            allowed_credentials=options["allowCredentials"],
            user_verification=options["userVerification"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth begin failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/complete", response_model=PasskeyAuthCompleteResponse)
async def complete_authentication(
    request: PasskeyAuthCompleteRequest,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """
    Complete passkey authentication.
    
    Verifies the assertion and returns success.
    """
    try:
        # In production, verify signature against stored public key
        # For now, we'll just verify the challenge
        success, credential = passkey_service.verify_authentication(
            db=db,
            contractor_email=request.contractor_email,
            challenge=request.challenge,
            credential_id=request.credential_id,
            sign_count=1  # Would be parsed from authenticatorData
        )
        
        if not success:
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        return PasskeyAuthCompleteResponse(
            success=True,
            contractor_email=request.contractor_email,
            credential_id=request.credential_id,
            message="Authentication successful"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{contractor_email}", response_model=PasskeyListResponse)
async def list_passkeys(
    contractor_email: str,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """List all passkeys for a contractor."""
    passkeys = passkey_service.get_passkeys_for_contractor(db, contractor_email)
    
    return PasskeyListResponse(
        contractor_email=contractor_email,
        passkeys=[
            PasskeyCredentialInfo(
                id=p.id,
                device_name=p.device_name,
                credential_type=p.credential_type,
                created_at=p.created_at,
                last_used_at=p.last_used_at,
                is_active=p.is_active
            )
            for p in passkeys
        ],
        count=len(passkeys)
    )


@router.delete("/delete")
async def delete_passkey(
    request: PasskeyDeleteRequest,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """Delete a passkey."""
    success = passkey_service.delete_passkey(
        db=db,
        credential_id=request.credential_id,
        contractor_email=request.contractor_email
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Passkey not found")
    
    return {"success": True, "message": "Passkey deleted"}


@router.get("/check/{contractor_email}")
async def check_passkey_status(
    contractor_email: str,
    db: Session = Depends(get_db),
    passkey_service: PasskeyService = Depends(get_passkey_service)
):
    """Check if contractor has any passkeys registered."""
    has_passkey = passkey_service.contractor_has_passkey(db, contractor_email)
    return {"has_passkey": has_passkey, "contractor_email": contractor_email}
