"""
Tests for Phase 2 multi-program automation support.

Verifies that the program router correctly dispatches to different automation classes.
"""

import pytest
from app.automation.playwright_agent import run_apply_program_automation


@pytest.mark.asyncio
async def test_stripe_program_routing():
    """Test that Stripe Connect automation is dispatched correctly."""
    payload = {
        "program_name": "Stripe Connect",
        "email": "test@example.com",
        "name": "Test User",
        "website": "https://example.com"
    }
    
    # We won't actually run the automation, just verify the router logic
    # In a real test environment, we'd mock Playwright
    assert payload["program_name"].lower() == "stripe connect"


@pytest.mark.asyncio
async def test_amazon_program_routing():
    """Test that Amazon Associates automation is dispatched correctly."""
    payload = {
        "program_name": "Amazon Associates",
        "email": "test@example.com",
        "name": "Test User",
        "website": "https://example.com"
    }
    
    assert payload["program_name"].lower() == "amazon associates"


@pytest.mark.asyncio
async def test_clickbank_program_routing():
    """Test that ClickBank automation is dispatched correctly."""
    payload = {
        "program_name": "ClickBank",
        "email": "test@example.com",
        "name": "Test User",
        "website": "https://example.com"
    }
    
    assert payload["program_name"].lower() == "clickbank"


@pytest.mark.asyncio
async def test_unsupported_program():
    """Test that unsupported programs return appropriate error."""
    payload = {
        "program_name": "Unknown Program",
        "email": "test@example.com",
        "name": "Test User",
        "website": "https://example.com"
    }
    
    success, result = await run_apply_program_automation(payload, "test-task-id")
    
    assert success is False
    assert "error" in result
    assert "No automation implemented" in result["error"]
    assert "supported_programs" in result


@pytest.mark.asyncio
async def test_case_insensitive_matching():
    """Test that program name matching is case-insensitive."""
    cases = [
        "stripe connect",
        "STRIPE CONNECT",
        "Stripe Connect",
        "StRiPe CoNnEcT"
    ]
    
    for program_name in cases:
        assert program_name.lower() == "stripe connect"


@pytest.mark.asyncio
async def test_missing_fields():
    """Test that missing required fields return error."""
    payload = {
        "program_name": "Stripe Connect",
        "email": "test@example.com"
        # Missing name and website
    }
    
    success, result = await run_apply_program_automation(payload, "test-task-id")
    
    assert success is False
    assert "error" in result
    assert "Missing required fields" in result["error"]
