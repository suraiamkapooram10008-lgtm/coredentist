"""
Field-Level Encryption for Sensitive Data
Encrypts API keys, payment tokens, and other sensitive fields
"""

from cryptography.fernet import Fernet
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FieldEncryption:
    """Handles encryption/decryption of sensitive database fields"""
    
    def __init__(self):
        """Initialize encryption with key from settings"""
        try:
            # Ensure ENCRYPTION_KEY is set and valid
            if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
                logger.warning("ENCRYPTION_KEY not set - encryption disabled")
                self.cipher = None
            else:
                self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.cipher = None
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return plaintext
        
        if not self.cipher:
            logger.warning("Encryption not available - storing plaintext")
            return plaintext
        
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            ciphertext: Encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext
        
        if not self.cipher:
            logger.warning("Encryption not available - returning as-is")
            return ciphertext
        
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Return ciphertext as-is if decryption fails (not encrypted or wrong key)
            return ciphertext


# Global encryption instance
encryption = FieldEncryption()


def generate_encryption_key() -> str:
    """
    Generate a new encryption key
    
    Returns:
        Base64-encoded encryption key
        
    Usage:
        python -c "from app.core.encryption import generate_encryption_key; print(generate_encryption_key())"
    """
    return Fernet.generate_key().decode()


def encrypt_value(value: str) -> str:
    """
    Encrypt a plaintext string (convenience function)
    
    Args:
        value: String to encrypt
        
    Returns:
        Encrypted string (base64 encoded), or original value if encryption unavailable
    """
    return encryption.encrypt(value)


def decrypt_value(value: str) -> str:
    """
    Decrypt an encrypted string (convenience function)
    
    Args:
        value: Encrypted string to decrypt
        
    Returns:
        Decrypted plaintext string, or original value if decryption unavailable
    """
    return encryption.decrypt(value)
