"""
Tenant boundary enforcement for multi-tenant security.

CRITICAL: Prevents cross-tenant privilege escalation.
Phase 10: Security Hardening - Tenant Boundary Fix
"""
from functools import wraps
from fastapi import HTTPException, Depends
from typing import Callable
import uuid

from app.models.user import User
from app.api.deps import get_current_user
from app.core.rbac import Role


def enforce_tenant_boundary(tenant_param_name: str = "tenant_id"):
    """
    Decorator to enforce tenant boundary for TENANT_ADMIN and below.
    
    CRITICAL SECURITY:
    Prevents cross-tenant escalation where TENANT_ADMIN of Tenant A
    cannot operate on resources of Tenant B.
    
    SYSTEM_ADMIN can operate across tenants (by design).
    
    Usage:
        @router.post("/api/v1/tenant/{tenant_id}/killswitch")
        @require_permission("killswitch:activate")
        @enforce_tenant_boundary("tenant_id")
        async def activate_killswitch(tenant_id: str, current_user = Depends(...)):
            # tenant_id is validated against current_user.tenant_id
            ...
    
    Args:
        tenant_param_name: Name of the path/query parameter containing tenant_id
    
    Raises:
        HTTPException: 403 if tenant boundary violated
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            # SYSTEM_ADMIN can cross tenant boundaries
            try:
                user_role = Role(current_user.role) if isinstance(current_user.role, str) else current_user.role
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=403,
                    detail={"error": "invalid_role", "message": "User has invalid or no role"}
                )
            
            if user_role == Role.SYSTEM_ADMIN:
                # SYSTEM_ADMIN bypass
                return await func(*args, current_user=current_user, **kwargs)
            
            # Extract requested tenant_id from parameters
            requested_tenant_id = kwargs.get(tenant_param_name)
            
            if not requested_tenant_id:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "missing_tenant_id", "message": f"Parameter '{tenant_param_name}' is required"}
                )
            
            # Normalize to UUID
            try:
                requested_tenant_uuid = uuid.UUID(requested_tenant_id)
                user_tenant_uuid = uuid.UUID(str(current_user.tenant_id))
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "invalid_tenant_id", "message": "Invalid tenant ID format"}
                )
            
            # Enforce boundary
            if user_tenant_uuid != requested_tenant_uuid:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "cross_tenant_access_denied",
                        "message": f"Cannot access resources of tenant {requested_tenant_id}",
                        "your_tenant_id": str(current_user.tenant_id)
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def enforce_resource_tenant_boundary(resource_tenant_id: uuid.UUID, current_user: User):
    """
    Service-layer tenant boundary check.
    
    Use this for defensive checks inside service functions.
    
    Example:
        def delete_task(db, task_id, current_user):
            task = db.query(Task).filter(Task.id == task_id).first()
            enforce_resource_tenant_boundary(task.tenant_id, current_user)
            # Safe to proceed
    
    Raises:
        HTTPException: 403 if boundary violated
    """
    # SYSTEM_ADMIN can cross boundaries
    try:
        user_role = Role(current_user.role) if isinstance(current_user.role, str) else current_user.role
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail="Invalid user role")
    
    if user_role == Role.SYSTEM_ADMIN:
        return  # Allowed
    
    # Enforce boundary
    user_tenant_uuid = uuid.UUID(str(current_user.tenant_id))
    if user_tenant_uuid != resource_tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cross_tenant_access_denied",
                "message": "Cannot access resource from different tenant"
            }
        )
