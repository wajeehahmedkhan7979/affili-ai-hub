"""
Security utilities for authentication and encryption.
Includes AES-256-GCM envelope encryption for credential storage.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.core.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """Derive an AES-256 key from a password using PBKDF2.
    
    Returns: (key, salt) tuple
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    return key, salt


def encrypt_secret(plaintext: str, key: Optional[str] = None) -> str:
    """
    Encrypt a secret using AES-256-GCM.
    
    Args:
        plaintext: The secret to encrypt
        key: Encryption key (uses ENCRYPTION_KEY from settings if not provided)
    
    Returns:
        Base64-encoded encrypted payload (nonce + ciphertext + tag)
    
    NOTE: KEY_ROTATION strategy - currently using static key from .env.
    TODO: Implement zero-knowledge proof system where:
    - Key is derived per-user from their authentication
    - Master key rotation triggers re-encryption
    - Consider using a KMS (AWS KMS, HashiCorp Vault) in production
    """
    if key is None:
        key = settings.ENCRYPTION_KEY
    
    # Derive key from provided key string
    derived_key, salt = derive_key(key)
    
    # Generate nonce
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    
    # Encrypt
    cipher = AESGCM(derived_key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
    
    # Combine: salt (16) + nonce (12) + ciphertext + tag (16)
    encrypted_payload = salt + nonce + ciphertext
    
    # Return as base64
    return base64.b64encode(encrypted_payload).decode('utf-8')


def decrypt_secret(encrypted: str, key: Optional[str] = None) -> str:
    """
    Decrypt a secret encrypted with encrypt_secret().
    
    Args:
        encrypted: Base64-encoded encrypted payload
        key: Decryption key (uses ENCRYPTION_KEY from settings if not provided)
    
    Returns:
        Decrypted plaintext secret
    
    Raises:
        ValueError: If decryption fails
    """
    if key is None:
        key = settings.ENCRYPTION_KEY
    
    try:
        # Decode from base64
        encrypted_payload = base64.b64decode(encrypted)
        
        # Extract components
        salt = encrypted_payload[:16]
        nonce = encrypted_payload[16:28]
        ciphertext = encrypted_payload[28:]
        
        # Derive key using the same salt
        derived_key, _ = derive_key(key, salt)
        
        # Decrypt
        cipher = AESGCM(derived_key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt secret: {str(e)}")


def verify_agent_key(api_key: str) -> bool:
    """Verify an agent API key. Currently uses simple string comparison.
    
    TODO: Implement database lookup for per-agent API keys with:
    - Agent table with hashed API keys
    - Rate limiting per agent
    - Agent capability tracking
    """
    return api_key == settings.AGENT_API_KEY
