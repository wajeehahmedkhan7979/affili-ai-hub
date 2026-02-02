"""
Failure classification for task errors.

Classifies raw error messages into meaningful categories.
"""

from typing import Dict, Any
import enum


class FailureType(str, enum.Enum):
    """Failure type enumeration for task errors."""
    CAPTCHA_BLOCKED = "CAPTCHA_BLOCKED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    SELECTOR_NOT_FOUND = "SELECTOR_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN = "UNKNOWN"


def classify_failure(error_message: str, logs: str = "") -> str:
    """
    Classify failure based on error message and logs.
    
    Args:
        error_message: Error message from task
        logs: Execution logs
        
    Returns:
        FailureType enum value as string
    """
    if not error_message:
        return FailureType.UNKNOWN.value
    
    error_lower = error_message.lower()
    logs_lower = logs.lower() if logs else ""
    
    # CAPTCHA already classified
    if "captcha" in error_lower or "captcha_detected" in error_lower:
        return FailureType.CAPTCHA_BLOCKED.value
    
    # Timeout patterns
    if any(kw in error_lower for kw in ["timeout", "timed out", "time out"]):
        return FailureType.TIMEOUT.value
    
    if any(kw in logs_lower for kw in ["timeout", "timed out"]):
        return FailureType.TIMEOUT.value
    
    # Network errors
    if any(kw in error_lower for kw in [
        "network", "connection", "refused", "unreachable",
        "dns", "resolve", "socket", "reset"
    ]):
        return FailureType.NETWORK_ERROR.value
    
    # Selector errors (Playwright-specific)
    if any(kw in error_lower for kw in [
        "selector", "element not found", "no element", 
        "locator", "not visible", "detached"
    ]):
        return FailureType.SELECTOR_NOT_FOUND.value
    
    if "element" in logs_lower and "not found" in logs_lower:
        return FailureType.SELECTOR_NOT_FOUND.value
    
    # Validation errors
    if "validation" in error_lower or "invalid" in error_lower:
        return FailureType.VALIDATION_ERROR.value
    
    # Default to unknown
    return FailureType.UNKNOWN.value


def get_failure_summary(failure_type: str) -> str:
    """
    Get human-readable summary for failure type.
    
    Args:
        failure_type: FailureType enum value
        
    Returns:
        Human-readable description
    """
    summaries = {
        FailureType.CAPTCHA_BLOCKED.value: "Task blocked by CAPTCHA challenge",
        FailureType.TIMEOUT.value: "Operation timed out",
        FailureType.NETWORK_ERROR.value: "Network connectivity issue",
        FailureType.SELECTOR_NOT_FOUND.value: "Page element not found",
        FailureType.VALIDATION_ERROR.value: "Input validation failed",
        FailureType.UNKNOWN.value: "Unknown error",
    }
    
    return summaries.get(failure_type, "Unknown error")
