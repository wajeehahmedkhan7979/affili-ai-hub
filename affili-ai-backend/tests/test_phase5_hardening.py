"""
Additional Phase 5 hardening tests - CAPTCHA and rate limiting.
"""

import pytest
from unittest.mock import AsyncMock
from playwright.async_api import Page
from fastapi import HTTPException
from app.automation.captcha_detector import detect_captcha
from app.core.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_captcha_detector_recaptcha():
    """Test CAPTCHA detection for reCAPTCHA iframe."""
    page = AsyncMock(spec=Page)
    page.url = "https://example.com/signup"
    
    # Mock iframe with reCAPTCHA
    mock_iframe = AsyncMock()
    mock_iframe.get_attribute = AsyncMock(return_value="https://www.google.com/recaptcha/api2/anchor")
    page.query_selector_all = AsyncMock(return_value=[mock_iframe])
    
    result = await detect_captcha(page)
    
    assert result["detected"] is True
    assert "recaptcha" in result["reason"].lower()


@pytest.mark.asyncio
async def test_captcha_detector_no_captcha():
    """Test CAPTCHA detector returns False when no CAPTCHA present."""
    page = AsyncMock(spec=Page)
    page.url = "https://example.com"
    page.query_selector_all = AsyncMock(return_value=[])
    page.query_selector = AsyncMock(return_value=None)
    page.inner_text = AsyncMock(return_value="Normal page content")
    
    result = await detect_captcha(page)
    
    assert result["detected"] is False
    assert result["reason"] == ""


def test_rate_limiter_allows_within_limit():
    """Test rate limiter allows requests within limit."""
    limiter = RateLimiter()
    limiter.limits["test"] = (3, 60)  # 3 per minute
    
    # Should not raise
    limiter.check_rate_limit("test", "user1")
    limiter.check_rate_limit("test", "user1")
    limiter.check_rate_limit("test", "user1")


def test_rate_limiter_blocks_over_limit():
    """Test rate limiter blocks requests exceeding limit."""
    limiter = RateLimiter()
    limiter.limits["test"] = (2, 60)
    
    limiter.check_rate_limit("test", "user1")
    limiter.check_rate_limit("test", "user1")
    
    # 3rd request should raise HTTP 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit("test", "user1")
    
    assert exc_info.value.status_code == 429


def test_rate_limiter_separate_users():
    """Test rate limiter tracks different users separately."""
    limiter = RateLimiter()
    limiter.limits["test"] = (2, 60)
    
    limiter.check_rate_limit("test", "user1")
    limiter.check_rate_limit("test", "user1")
    
    # user2 should have full quota
    limiter.check_rate_limit("test", "user2")
    limiter.check_rate_limit("test", "user2")
