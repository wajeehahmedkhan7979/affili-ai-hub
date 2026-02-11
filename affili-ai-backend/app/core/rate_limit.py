"""
Tenant-aware rate limiting for multi-tenant API protection.
Phase 10: Security Hardening
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.tenant import get_tenant_id


def get_rate_limit_key():
    """
    Rate limit key function that uses tenant ID when available.
    
    This ensures rate limits are applied per-tenant, not per-IP.
    Critical for multi-tenant fairness and preventing noisy neighbors.
    
    Returns:
        str: Rate limit key (tenant:{id} or ip:{address})
    """
    try:
        tenant_id = get_tenant_id()
        if tenant_id:
            return f"tenant:{tenant_id}"
    except:
        pass
    
    # Fallback to IP for unauthenticated requests
    ip = get_remote_address()
    return f"ip:{ip}"


from app.core.config import settings

# Configure tenant-aware limiter
# Use Redis if available, otherwise fallback to memory (dev only)
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000/hour"],  # Global default
    storage_uri=storage_uri,
)


# Common rate limit constants (use in decorators)
class RateLimits:
    """Standard rate limits for different endpoint types."""
    
    # Task operations (high volume)
    TASK_CREATE = "100/minute"
    TASK_LIST = "200/minute"
    TASK_UPDATE = "100/minute"
    
    # Discovery operations (expensive)
    DISCOVERY = "10/minute"
    PROGRAM_SCRAPE = "20/minute"
    
    # Auth operations (brute-force prevention)
    LOGIN = "10/minute"
    REGISTER = "5/minute"
    PASSWORD_RESET = "3/minute"
    
    # Admin operations
    KILLSWITCH = "5/minute"
    ADMIN_ACTION = "50/minute"
    
    # Read operations (lenient)
    READ_ONLY = "500/minute"
