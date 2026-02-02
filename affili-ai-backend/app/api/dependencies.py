"""
API dependencies for multi-tenancy and security.
"""

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid
from typing import Optional, List

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.tenant import set_tenant_id, get_tenant_id, DEFAULT_TENANT_ID
from app.services.auth_service import decode_token


async def verify_tenant(
    x_tenant_id: Optional[str] = Header(DEFAULT_TENANT_ID, alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
) -> str:
    """
    Verify tenant ID from header and set in context.
    
    Args:
        x_tenant_id: Tenant ID from X-Tenant-ID header
        db: Database session
        
    Returns:
        str: Validated tenant ID
    """
    if not x_tenant_id:
        x_tenant_id = DEFAULT_TENANT_ID
        
    # Validate UUID format
    try:
        tenant_uuid = uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    
    # Check if tenant exists
    # Optimization: Cache this lookup or skip for default tenant if we know it exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid, Tenant.is_active == True).first()
    
    if not tenant:
        # If accessing default tenant and it's missing (e.g. fresh DB), consider auto-creating or erroring
        # For now, strict check
        raise HTTPException(status_code=404, detail="Tenant not found or inactive")
    
    # Set in context contextvar
    set_tenant_id(str(tenant_uuid))
    
    return str(tenant_uuid)


from app.models.user import User, UserRole
from app.core.tenant import get_tenant_id

# JWT OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

async def get_current_user(
    tenant_id: str = Depends(verify_tenant),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT or Identity Header (fallback).
    Also sets tenant context (already set by verify_tenant).
    """
    tenant_uuid = uuid.UUID(tenant_id)
    user = None

    # 1. Try JWT first
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            tid = payload.get("tid")
            
            # Cross-tenant safety check
            if tid != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token tenant mismatch"
                )
            
            user = db.query(User).filter(
                User.id == uuid.UUID(user_id),
                User.tenant_id == tenant_uuid,
                User.is_active == True
            ).first()

    # 2. Fallback to Header identity if no JWT or JWT failed
    if not user and x_user_email:
        user = db.query(User).filter(
            User.tenant_id == tenant_uuid,
            User.email == x_user_email,
            User.is_active == True
        ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user


def require_roles(*allowed_roles: UserRole):
    """
    Dependency to enforce role-based access control.
    """
    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions. Required one of: {[r.value for r in allowed_roles]}"
            )
        return user
    return guard
