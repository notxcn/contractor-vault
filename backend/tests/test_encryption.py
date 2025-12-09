"""
Contractor Vault - Encryption Service Tests
"""
import pytest
from app.services.encryption import EncryptionService, EncryptionError


class TestEncryptionService:
    """Test suite for encryption service."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt -> decrypt returns original value."""
        service = EncryptionService()
        
        original = "my-super-secret-password-123!"
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original.encode()
    
    def test_encrypt_empty_string_raises(self):
        """Test that encrypting empty string raises error."""
        service = EncryptionService()
        
        with pytest.raises(EncryptionError):
            service.encrypt("")
    
    def test_decrypt_empty_raises(self):
        """Test that decrypting empty bytes raises error."""
        service = EncryptionService()
        
        with pytest.raises(EncryptionError):
            service.decrypt(b"")
    
    def test_decrypt_invalid_token_raises(self):
        """Test that decrypting invalid token raises error."""
        service = EncryptionService()
        
        with pytest.raises(EncryptionError):
            service.decrypt(b"not-a-valid-fernet-token")
    
    def test_different_plaintexts_produce_different_ciphertexts(self):
        """Test that different inputs produce different outputs."""
        service = EncryptionService()
        
        encrypted1 = service.encrypt("password1")
        encrypted2 = service.encrypt("password2")
        
        assert encrypted1 != encrypted2
    
    def test_same_plaintext_produces_different_ciphertexts(self):
        """Test that same input produces different outputs (due to IV)."""
        service = EncryptionService()
        
        encrypted1 = service.encrypt("same-password")
        encrypted2 = service.encrypt("same-password")
        
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert service.decrypt(encrypted1) == service.decrypt(encrypted2)
