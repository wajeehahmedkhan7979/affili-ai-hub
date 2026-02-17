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

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    tenant_name: Optional[str] = "Default Tenant"

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    tenant_id: uuid.UUID
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str
