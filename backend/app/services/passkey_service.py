"""
Contractor Vault - Passkey Service
WebAuthn/FIDO2 authentication service
"""
import base64
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.passkey import PasskeyCredential, PasskeyChallenge
from app.config import get_settings

logger = logging.getLogger(__name__)


class PasskeyService:
    """
    Service for WebAuthn passkey operations.
    
    Handles:
    - Challenge generation for registration/authentication
    - Credential storage and retrieval
    - Sign count verification
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.rp_id = "localhost"  # Change in production
        self.rp_name = "Contractor Vault"
        self.challenge_timeout_seconds = 300  # 5 minutes
    
    def generate_challenge(self) -> str:
        """Generate a random challenge for WebAuthn ceremony."""
        challenge_bytes = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    def create_registration_challenge(
        self,
        db: Session,
        contractor_email: str
    ) -> dict:
        """
        Create a registration challenge for a contractor.
        
        Returns WebAuthn PublicKeyCredentialCreationOptions.
        """
        challenge = self.generate_challenge()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.challenge_timeout_seconds)
        
        # Store challenge
        challenge_record = PasskeyChallenge(
            challenge=challenge,
            challenge_type="registration",
            contractor_email=contractor_email,
            expires_at=expires_at
        )
        db.add(challenge_record)
        db.commit()
        
        # Create user ID (hash of email)
        import hashlib
        user_id = base64.urlsafe_b64encode(
            hashlib.sha256(contractor_email.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        return {
            "challenge": challenge,
            "rp": {
                "id": self.rp_id,
                "name": self.rp_name
            },
            "user": {
                "id": user_id,
                "name": contractor_email,
                "displayName": contractor_email.split('@')[0]
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},   # ES256
                {"type": "public-key", "alg": -257}  # RS256
            ],
            "timeout": self.challenge_timeout_seconds * 1000,
            "attestation": "none",
            "authenticatorSelection": {
                "authenticatorAttachment": "platform",
                "userVerification": "preferred",
                "residentKey": "preferred"
            }
        }
    
    def verify_and_store_credential(
        self,
        db: Session,
        contractor_email: str,
        challenge: str,
        credential_id: str,
        public_key: bytes,
        sign_count: int,
        device_name: str = "My Device",
        aaguid: Optional[str] = None
    ) -> PasskeyCredential:
        """
        Verify registration challenge and store credential.
        
        Returns the stored PasskeyCredential.
        """
        # Verify challenge exists and is valid
        challenge_record = db.query(PasskeyChallenge).filter(
            PasskeyChallenge.challenge == challenge,
            PasskeyChallenge.contractor_email == contractor_email,
            PasskeyChallenge.challenge_type == "registration",
            PasskeyChallenge.is_used == False
        ).first()
        
        if not challenge_record or not challenge_record.is_valid():
            raise ValueError("Invalid or expired challenge")
        
        # Mark challenge as used
        challenge_record.is_used = True
        
        # Store credential
        credential = PasskeyCredential(
            contractor_email=contractor_email,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            device_name=device_name,
            aaguid=aaguid
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
        
        logger.info(f"Registered passkey for {contractor_email}: {device_name}")
        return credential
    
    def create_authentication_challenge(
        self,
        db: Session,
        contractor_email: str,
        token_id: Optional[str] = None
    ) -> dict:
        """
        Create an authentication challenge.
        
        Returns WebAuthn PublicKeyCredentialRequestOptions.
        """
        challenge = self.generate_challenge()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.challenge_timeout_seconds)
        
        # Store challenge
        challenge_record = PasskeyChallenge(
            challenge=challenge,
            challenge_type="authentication",
            contractor_email=contractor_email,
            token_id=token_id,
            expires_at=expires_at
        )
        db.add(challenge_record)
        db.commit()
        
        # Get allowed credentials for this contractor
        credentials = db.query(PasskeyCredential).filter(
            PasskeyCredential.contractor_email == contractor_email,
            PasskeyCredential.is_active == True
        ).all()
        
        allowed_credentials = [
            {
                "type": "public-key",
                "id": cred.credential_id
            }
            for cred in credentials
        ]
        
        return {
            "challenge": challenge,
            "rpId": self.rp_id,
            "timeout": self.challenge_timeout_seconds * 1000,
            "userVerification": "preferred",
            "allowCredentials": allowed_credentials
        }
    
    def verify_authentication(
        self,
        db: Session,
        contractor_email: str,
        challenge: str,
        credential_id: str,
        sign_count: int
    ) -> Tuple[bool, PasskeyCredential]:
        """
        Verify an authentication response.
        
        Returns (success, credential) tuple.
        """
        # Verify challenge
        challenge_record = db.query(PasskeyChallenge).filter(
            PasskeyChallenge.challenge == challenge,
            PasskeyChallenge.contractor_email == contractor_email,
            PasskeyChallenge.challenge_type == "authentication",
            PasskeyChallenge.is_used == False
        ).first()
        
        if not challenge_record or not challenge_record.is_valid():
            return False, None
        
        # Get credential
        credential = db.query(PasskeyCredential).filter(
            PasskeyCredential.credential_id == credential_id,
            PasskeyCredential.contractor_email == contractor_email,
            PasskeyCredential.is_active == True
        ).first()
        
        if not credential:
            return False, None
        
        # Verify sign count (prevent replay attacks)
        if sign_count <= credential.sign_count:
            logger.warning(f"Sign count mismatch for {contractor_email}: got {sign_count}, expected > {credential.sign_count}")
            # Could indicate cloned authenticator - flag but don't fail
        
        # Update records
        challenge_record.is_used = True
        credential.sign_count = sign_count
        credential.last_used_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Passkey authentication successful for {contractor_email}")
        return True, credential
    
    def get_passkeys_for_contractor(
        self,
        db: Session,
        contractor_email: str
    ) -> list[PasskeyCredential]:
        """Get all passkeys for a contractor."""
        return db.query(PasskeyCredential).filter(
            PasskeyCredential.contractor_email == contractor_email
        ).all()
    
    def delete_passkey(
        self,
        db: Session,
        credential_id: str,
        contractor_email: str
    ) -> bool:
        """Delete a passkey by credential ID."""
        credential = db.query(PasskeyCredential).filter(
            PasskeyCredential.credential_id == credential_id,
            PasskeyCredential.contractor_email == contractor_email
        ).first()
        
        if not credential:
            return False
        
        db.delete(credential)
        db.commit()
        logger.info(f"Deleted passkey {credential_id} for {contractor_email}")
        return True
    
    def contractor_has_passkey(
        self,
        db: Session,
        contractor_email: str
    ) -> bool:
        """Check if contractor has any active passkeys."""
        return db.query(PasskeyCredential).filter(
            PasskeyCredential.contractor_email == contractor_email,
            PasskeyCredential.is_active == True
        ).count() > 0


# Singleton instance
_passkey_service = None

def get_passkey_service() -> PasskeyService:
    """Get singleton passkey service instance."""
    global _passkey_service
    if _passkey_service is None:
        _passkey_service = PasskeyService()
    return _passkey_service
