"""
Contractor Vault - Token Service
JWT generation and validation for session tokens
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Raised when token operations fail."""
    pass


class TokenService:
    """
    JWT token service for access token generation and validation.
    
    SOC2 Requirements:
    - Tokens have explicit expiration
    - Signing key from environment
    - Claims include audit information
    """
    
    def __init__(self):
        """Initialize with JWT settings from environment."""
        self._settings = get_settings()
        logger.info("Token service initialized")
    
    def create_access_jwt(
        self,
        token_id: str,
        credential_id: str,
        contractor_email: str,
        expires_at: datetime,
        additional_claims: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Create a signed JWT for session access.
        
        Args:
            token_id: The session token ID in database
            credential_id: The credential being accessed
            contractor_email: Email of the contractor
            expires_at: Token expiration time
            additional_claims: Optional extra claims
            
        Returns:
            Signed JWT string
        """
        now = datetime.now(timezone.utc)
        
        claims = {
            # Standard JWT claims
            "iss": self._settings.jwt_issuer,
            "sub": contractor_email,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "nbf": int(now.timestamp()),  # Not valid before now
            
            # Custom claims
            "token_id": token_id,
            "credential_id": credential_id,
            "purpose": "credential_access",
        }
        
        if additional_claims:
            claims.update(additional_claims)
        
        try:
            token = jwt.encode(
                claims,
                self._settings.jwt_secret,
                algorithm=self._settings.jwt_algorithm
            )
            logger.info(f"Created access JWT for token_id={token_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create JWT: {e}")
            raise TokenError("Failed to create access token") from e
    
    def validate_access_jwt(self, token: str) -> dict[str, Any]:
        """
        Validate and decode a JWT.
        
        Args:
            token: The JWT string to validate
            
        Returns:
            Decoded claims dictionary
            
        Raises:
            TokenError: If token is invalid, expired, or malformed
        """
        try:
            claims = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
                issuer=self._settings.jwt_issuer
            )
            logger.debug(f"Validated JWT for token_id={claims.get('token_id')}")
            return claims
        except jwt.ExpiredSignatureError:
            logger.warning("JWT validation failed: Token expired")
            raise TokenError("Token has expired")
        except jwt.JWTClaimsError as e:
            logger.warning(f"JWT validation failed: Invalid claims - {e}")
            raise TokenError("Invalid token claims")
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise TokenError("Invalid token")
    
    def calculate_expiry(self, duration_minutes: int) -> datetime:
        """
        Calculate token expiry time with validation.
        
        Args:
            duration_minutes: Requested duration in minutes
            
        Returns:
            Expiry datetime in UTC
            
        Raises:
            TokenError: If duration exceeds maximum allowed
        """
        if duration_minutes <= 0:
            raise TokenError("Duration must be positive")
        
        if duration_minutes > self._settings.max_token_duration_minutes:
            raise TokenError(
                f"Duration exceeds maximum of {self._settings.max_token_duration_minutes} minutes"
            )
        
        return datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)


@lru_cache()
def get_token_service() -> TokenService:
    """Get cached token service instance."""
    return TokenService()
