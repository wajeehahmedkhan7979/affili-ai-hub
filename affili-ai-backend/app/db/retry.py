"""
Transaction retry decorator for handling database deadlocks and concurrency collisions.
Production-grade resilience for high-concurrency scenarios.
"""
import time
import functools
from sqlalchemy.exc import OperationalError, DBAPIError
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def retry_on_deadlock(
    max_attempts: int = 3,
    backoff_ms: int = 100,
    backoff_multiplier: float = 2.0
):
    """
    Retry decorator for database operations that may encounter deadlocks.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_ms: Initial backoff delay in milliseconds (default: 100ms)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
    
    Usage:
        @retry_on_deadlock(max_attempts=5, backoff_ms=50)
        def claim_task(db, agent_id):
            return find_and_claim_task(db, agent_id)
    
    Handles:
        - Postgres deadlock detection
        - Lock timeout errors
        - Serialization failures
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except (OperationalError, DBAPIError) as e:
                    error_msg = str(e).lower()
                    
                    # Check if error is retryable
                    is_deadlock = any(keyword in error_msg for keyword in [
                        'deadlock',
                        'lock timeout',
                        'could not serialize',
                        'concurrent update'
                    ])
                    
                    if not is_deadlock:
                        # Not a deadlock, re-raise immediately
                        raise
                    
                    # Last attempt - don't retry
                    if attempt >= max_attempts - 1:
                        raise
                    
                    # Calculate exponential backoff
                    delay_ms = backoff_ms * (backoff_multiplier ** attempt)
                    time.sleep(delay_ms / 1000.0)
                    
                    last_exception = e
                    # Log retry attempt (production systems should use proper logger)
                    # logger.warning(f"Deadlock detected, retry {attempt + 1}/{max_attempts}")
                    continue
            
            # Should never reach here, but for safety
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_on_connection_error(
    max_attempts: int = 3,
    backoff_ms: int = 500
):
    """
    Retry decorator for transient connection errors.
    
    Handles:
        - Connection pool exhaustion
        - Network timeouts
        - Database restart scenarios
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except (OperationalError, DBAPIError) as e:
                    error_msg = str(e).lower()
                    
                    is_connection_error = any(keyword in error_msg for keyword in [
                        'connection',
                        'timeout',
                        'pool',
                        'network'
                    ])
                    
                    if not is_connection_error or attempt >= max_attempts - 1:
                        raise
                    
                    time.sleep(backoff_ms / 1000.0)
                    continue
            
        return wrapper
    return decorator
