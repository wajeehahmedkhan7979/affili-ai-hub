"""
Schemas for authentication.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    tenant_id: uuid.UUID

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str
