"""
Authentication service for password hashing and JWT management.
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
import uuid

from app.core.time import utcnow
from app.core.config import settings

# Configuration loaded from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    result = pwd_context.verify(plain_password, hashed_password)
    return result

def create_access_token(
    user_id: uuid.UUID, 
    tenant_id: uuid.UUID, 
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a short-lived access token."""
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    user_id: uuid.UUID,
    version: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a long-lived refresh token."""
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user_id),
        "ver": version,
        "exp": expire,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate a JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return {}

def authenticate_via_saml_sso(saml_resp: str) -> dict:
    """
    Placeholder for enterprise SAML/SSO integration.
    TODO: Integrate with python3-saml or similar library.
    """
    # Logic to parse XML, verify signature, and extract assertions
    return {
        "user_email": "sso_user@enterprise.com",
        "tenant_id": "saml_mapped_tenant_id",
        "groups": ["marketing_admins"]
    }