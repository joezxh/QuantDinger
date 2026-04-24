import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CryptoUtils:
    """
    Utility for encrypting and decrypting sensitive data (API Keys)
    Uses AES-256-GCM for authenticated encryption.
    """
    
    _secret = os.getenv('LLM_KEY_SECRET', 'quantdinger-default-llm-secret-key-change-me')
    _salt = b'quantdinger_salt_fixed' # Fixed salt for deterministic key derivation from secret

    @classmethod
    def _get_aes_key(cls):
        """Derive a 256-bit AES key from the secret string"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=cls._salt,
            iterations=100000,
        )
        return kdf.derive(cls._secret.encode())

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.
        Returns base64 encoded string: b64(nonce + ciphertext + tag)
        """
        if not plaintext:
            return ""
        
        try:
            aes_key = cls._get_aes_key()
            aesgcm = AESGCM(aes_key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
            
            # Combine nonce and ciphertext
            result = nonce + ciphertext
            return base64.b64encode(result).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        Decrypt ciphertext.
        Expected format: base64 encoded (nonce + ciphertext + tag)
        """
        if not encrypted_text:
            return ""
        
        try:
            data = base64.b64decode(encrypted_text.encode('utf-8'))
            nonce = data[:12]
            ciphertext = data[12:]
            
            aes_key = cls._get_aes_key()
            aesgcm = AESGCM(aes_key)
            
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # If decryption fails, it might be an unencrypted key (for migration)
            # but for safety in this new system, we should probably raise
            raise

crypto_utils = CryptoUtils
