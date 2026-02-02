"""
Security utilities for authentication and encryption.
Includes AES-256-GCM envelope encryption for credential storage.
"""
import os
import base64
import ipaddress
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

settings = get_settings()

class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access based on IP allowlists."""
    def __init__(self, app, allowlist: Optional[List[str]] = None):
        super().__init__(app)
        self.allowlist = allowlist or []
        self.allowed_networks = [ipaddress.ip_network(net) for net in self.allowlist]

    async def dispatch(self, request: Request, call_next):
        if not self.allowed_networks:
            return await call_next(request)
            
        client_ip = ipaddress.ip_address(request.client.host)
        is_allowed = any(client_ip in net for net in self.allowed_networks)
        
        if not is_allowed:
            raise HTTPException(status_code=403, detail="IP address not allowed")
            
        return await call_next(request)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    """Derive an AES-256 key from a password using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_secret(plaintext: str, key: Optional[str] = None) -> str:
    """Encrypt a secret using AES-256-GCM."""
    if key is None:
        key = settings.ENCRYPTION_KEY
    
    derived_key, salt = derive_key(key)
    nonce = os.urandom(12)
    cipher = AESGCM(derived_key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
    encrypted_payload = salt + nonce + ciphertext
    return base64.b64encode(encrypted_payload).decode('utf-8')

def decrypt_secret(encrypted: str, key: Optional[str] = None) -> str:
    """Decrypt a secret encrypted with encrypt_secret()."""
    if key is None:
        key = settings.ENCRYPTION_KEY
    
    try:
        encrypted_payload = base64.b64decode(encrypted)
        salt = encrypted_payload[:16]
        nonce = encrypted_payload[16:28]
        ciphertext = encrypted_payload[28:]
        derived_key, _ = derive_key(key, salt)
        cipher = AESGCM(derived_key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt secret: {str(e)}")

def verify_agent_key(api_key: str) -> bool:
    """Verify an agent API key."""
    return api_key == settings.AGENT_API_KEY
