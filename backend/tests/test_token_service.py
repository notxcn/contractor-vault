"""
Contractor Vault - Token Service Tests
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.token_service import TokenService, TokenError


class TestTokenService:
    """Test suite for token service."""
    
    def test_create_and_validate_jwt(self):
        """Test JWT creation and validation roundtrip."""
        service = TokenService()
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        jwt = service.create_access_jwt(
            token_id="test-token-123",
            credential_id="cred-456",
            contractor_email="test@example.com",
            expires_at=expires_at,
        )
        
        claims = service.validate_access_jwt(jwt)
        
        assert claims["token_id"] == "test-token-123"
        assert claims["credential_id"] == "cred-456"
        assert claims["sub"] == "test@example.com"
    
    def test_expired_jwt_raises(self):
        """Test that expired JWT raises error."""
        service = TokenService()
        
        # Create token that expired 1 hour ago
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        jwt = service.create_access_jwt(
            token_id="test-token",
            credential_id="cred-123",
            contractor_email="test@example.com",
            expires_at=expires_at,
        )
        
        with pytest.raises(TokenError, match="expired"):
            service.validate_access_jwt(jwt)
    
    def test_invalid_jwt_raises(self):
        """Test that invalid JWT raises error."""
        service = TokenService()
        
        with pytest.raises(TokenError):
            service.validate_access_jwt("not.a.valid.jwt")
    
    def test_calculate_expiry_positive(self):
        """Test expiry calculation with valid duration."""
        service = TokenService()
        
        before = datetime.now(timezone.utc)
        expiry = service.calculate_expiry(60)
        after = datetime.now(timezone.utc)
        
        assert expiry > before
        assert expiry < after + timedelta(minutes=61)
    
    def test_calculate_expiry_zero_raises(self):
        """Test that zero duration raises error."""
        service = TokenService()
        
        with pytest.raises(TokenError, match="positive"):
            service.calculate_expiry(0)
    
    def test_calculate_expiry_negative_raises(self):
        """Test that negative duration raises error."""
        service = TokenService()
        
        with pytest.raises(TokenError, match="positive"):
            service.calculate_expiry(-30)
    
    def test_calculate_expiry_exceeds_max_raises(self):
        """Test that excessive duration raises error."""
        service = TokenService()
        
        with pytest.raises(TokenError, match="maximum"):
            service.calculate_expiry(99999)
