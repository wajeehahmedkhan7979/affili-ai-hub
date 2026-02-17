"""
Core time utility for the application.
Centralizes time handling to ensure consistent timezone-aware UTC usage.
"""
from datetime import datetime, timezone

def utcnow() -> datetime:
    """
    Get current UTC time with timezone information.
    Replaces datetime.utcnow() which returns naive datetime.
    
    Returns:
        datetime: Current time in UTC with tzinfo=timezone.utc
    """
    return datetime.now(timezone.utc)
