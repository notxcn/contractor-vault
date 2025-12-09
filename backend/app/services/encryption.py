"""
Contractor Vault - Encryption Service
Fernet symmetric encryption for credential storage
"""
import logging
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class EncryptionService:
    """
    Fernet symmetric encryption service.
    
    SOC2 Requirements:
    - Keys loaded from environment variables only
    - No plaintext passwords in logs
    - Fail securely on decryption errors
    
    Usage:
        service = EncryptionService()
        encrypted = service.encrypt("my-password")
        decrypted = service.decrypt(encrypted)
    """
    
    def __init__(self):
        """Initialize with Fernet key from environment."""
        settings = get_settings()
        try:
            self._fernet = Fernet(settings.fernet_key.encode())
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise EncryptionError("Invalid encryption key configuration") from e
    
    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Encrypted bytes (Fernet token)
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            raise EncryptionError("Cannot encrypt empty string")
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
            logger.debug("Successfully encrypted value")
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError("Failed to encrypt value") from e
    
    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt a Fernet token back to plaintext.
        
        Args:
            ciphertext: The encrypted bytes to decrypt
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            EncryptionError: If decryption fails (invalid token, wrong key, etc.)
        """
        if not ciphertext:
            raise EncryptionError("Cannot decrypt empty ciphertext")
        
        try:
            decrypted = self._fernet.decrypt(ciphertext)
            logger.debug("Successfully decrypted value")
            return decrypted.decode("utf-8")
        except InvalidToken as e:
            logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
            raise EncryptionError("Invalid encryption token") from e
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError("Failed to decrypt value") from e
    
    def rotate_key(self, old_ciphertext: bytes, new_fernet: Fernet) -> bytes:
        """
        Re-encrypt data with a new key (for key rotation).
        
        Args:
            old_ciphertext: Data encrypted with current key
            new_fernet: Fernet instance with new key
            
        Returns:
            Data encrypted with new key
        """
        plaintext = self.decrypt(old_ciphertext)
        return new_fernet.encrypt(plaintext.encode("utf-8"))


@lru_cache()
def get_encryption_service() -> EncryptionService:
    """Get cached encryption service instance."""
    return EncryptionService()
