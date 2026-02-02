"""
Tenant context management for request-scoped isolation.
"""

from contextvars import ContextVar
from typing import Optional

# Default tenant ID for backward compatibility
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"

# Context variable to store current tenant ID
_current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default=DEFAULT_TENANT_ID)


def get_tenant_id() -> str:
    """
    Get the current tenant ID from context.
    
    Returns:
        str: Current tenant ID or default if not set
    """
    return _current_tenant_id.get()


def set_tenant_id(tenant_id: str) -> None:
    """
    Set the current tenant ID in context.
    
    Args:
        tenant_id: Tenant UUID string
    """
    if not tenant_id:
        tenant_id = DEFAULT_TENANT_ID
    _current_tenant_id.set(str(tenant_id))


def reset_tenant_id() -> None:
    """Reset tenant ID to default."""
    _current_tenant_id.set(DEFAULT_TENANT_ID)
