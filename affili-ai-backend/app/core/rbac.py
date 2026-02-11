"""
Role-Based Access Control (RBAC) framework for AFFILI-AI HUB.

Defines role hierarchy, permissions, and enforcement decorators.
Phase 10: Security Hardening
"""
from enum import Enum
from typing import List, Callable
from functools import wraps
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.api.deps import get_current_user


class Role(str, Enum):
    """Role hierarchy for RBAC."""
    SYSTEM_ADMIN = "SYSTEM_ADMIN"      # Full system access
    TENANT_ADMIN = "TENANT_ADMIN"      # Tenant-wide administration
    OPERATOR = "OPERATOR"              # Can create tasks, view logs
    VIEWER = "VIEWER"                  # Read-only access


# Permission matrix: permission -> allowed roles
PERMISSIONS = {
    # Task operations
    "tasks:create": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR],
    "tasks:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR, Role.VIEWER],
    "tasks:delete": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    
    # Kill-switch (critical governance)
    "killswitch:activate": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "killswitch:deactivate": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    
    # Audit logs
    "audit_logs:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "audit_logs:export": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    
    # User management
    "users:create": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "users:update": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "users:delete": [Role.SYSTEM_ADMIN],
    "users:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR],
    
    # Billing & usage
    "billing:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "billing:update": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    
    # Programs & applications
    "programs:create": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR],
    "programs:update": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR],
    "programs:delete": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
    "programs:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR, Role.VIEWER],
    
    # Agent management
    "agents:view": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR],
    "agents:control": [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN],
}


def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has required permission.
    
    Args:
        user: User object with role attribute
        permission: Permission string (e.g., "tasks:create")
    
    Returns:
        bool: True if user's role is allowed for this permission
    """
    if not user or not hasattr(user, 'role'):
        return False
    
    allowed_roles = PERMISSIONS.get(permission, [])
    
    # Convert user.role to Role enum if it's a string
    try:
        user_role = Role(user.role) if isinstance(user.role, str) else user.role
    except ValueError:
        return False
    
    return user_role in allowed_roles


def require_permission(permission: str):
    """
    Decorator to enforce permission on FastAPI endpoints.
    
    Usage:
        @router.post("/api/v1/tasks")
        @require_permission("tasks:create")
        async def create_task(current_user: User = Depends(get_current_user)):
            ...
    
    Args:
        permission: Permission string to require
    
    Raises:
        HTTPException: 403 if user lacks permission
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_permissions",
                        "message": f"Permission '{permission}' required",
                        "required_roles": [r.value for r in PERMISSIONS.get(permission, [])],
                        "your_role": current_user.role if current_user else None
                    }
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_role(role: Role):
    """
    Decorator to enforce minimum role level.
    
    Simpler than permission-based, useful for broad access control.
    
    Usage:
        @require_role(Role.TENANT_ADMIN)
        async def admin_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            try:
                user_role = Role(current_user.role) if isinstance(current_user.role, str) else current_user.role
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=403,
                    detail={"error": "invalid_role", "message": "User has invalid or no role"}
                )
            
            # Role hierarchy: SYSTEM_ADMIN > TENANT_ADMIN > OPERATOR > VIEWER
            role_hierarchy = [Role.SYSTEM_ADMIN, Role.TENANT_ADMIN, Role.OPERATOR, Role.VIEWER]
            
            if role_hierarchy.index(user_role) > role_hierarchy.index(role):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_role",
                        "message": f"Minimum role '{role.value}' required",
                        "your_role": user_role.value
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
