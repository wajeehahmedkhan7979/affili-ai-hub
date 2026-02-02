"""
Simple in-process rate limiter using token bucket algorithm.

No external dependencies (Redis) required.
"""

from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException
import threading


class RateLimiter:
    """Thread-safe in-process rate limiter."""
    
    def __init__(self):
        self._buckets: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self._lock = threading.Lock()
        
        # Rate limit configurations: (max_requests, window_seconds)
        self.limits = {
            "task_creation": (10, 60),        # 10 per minute
            "discovery": (2, 300),            # 2 per 5 minutes
            "applications": (5, 60),          # 5 per minute
        }
    
    def check_rate_limit(self, key: str, identifier: str = "default") -> None:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., 'task_creation')
            identifier: Client identifier (e.g., IP, user ID)
            
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if key not in self.limits:
            return  # No limit configured for this key
        
        max_requests, window_seconds = self.limits[key]
        
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Get request timestamps for this identifier and key
            bucket = self._buckets[key][identifier]
            
            # Remove expired timestamps
            bucket[:] = [ts for ts in bucket if ts > cutoff]
            
            # Check if limit exceeded
            if len(bucket) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {key}. Max {max_requests} requests per {window_seconds} seconds."
                )
            
            # Add current timestamp
            bucket.append(now)
    
    def reset(self, key: str = None, identifier: str = None) -> None:
        """Reset rate limit buckets (useful for testing)."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            elif identifier is None:
                self._buckets[key].clear()
            else:
                self._buckets[key][identifier].clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def check_rate_limit(key: str, identifier: str = "default") -> None:
    """
    Convenience function to check rate limit.
    
    Args:
        key: Rate limit key (e.g., 'task_creation')
        identifier: Client identifier
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    _rate_limiter.check_rate_limit(key, identifier)
