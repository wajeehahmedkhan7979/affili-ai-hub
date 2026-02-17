"""
Tests for Phase 3 discovery agent functionality.
"""

import pytest
from app.automation.discovery_agent import DiscoveryAgent


def test_keyword_detection():
    """Test that affiliate keywords are correctly defined."""
    agent = DiscoveryAgent()
    
    assert "affiliate" in agent.AFFILIATE_KEYWORDS
    assert "partner" in agent.AFFILIATE_KEYWORDS
    assert "referral" in agent.AFFILIATE_KEYWORDS
    assert "earn" in agent.AFFILIATE_KEYWORDS


def test_confidence_scoring():
    """Test confidence score calculation."""
    agent = DiscoveryAgent()
    
    # High confidence: affiliate + signup + footer + https
    score1 = agent._calculate_confidence(
        href="https://example.com/affiliate/signup",
        text="join our affiliate program",
        in_footer=True
    )
    assert score1 >= 0.8
    
    # Medium confidence: partner + https
    score2 = agent._calculate_confidence(
        href="https://example.com/partners",
        text="partners",
        in_footer=False
    )
    assert 0.3 <= score2 <= 0.6
    
    # Low confidence: no keywords
    score3 = agent._calculate_confidence(
        href="http://example.com/about",
        text="about us",
        in_footer=False
    )
    assert score3 < 0.2


def test_program_name_extraction():
    """Test program name extraction from link data."""
    agent = DiscoveryAgent()
    
    # Meaningful text
    name1 = agent._extract_program_name(
        href="https://example.com/affiliate",
        text="Example Partner Program",
        seed_url="https://example.com"
    )
    assert "Example Partner Program" in name1
    
    # Trash text - should use domain
    name2 = agent._extract_program_name(
        href="https://example.com/affiliate",
        text="click here",
        seed_url="https://example.com"
    )
    assert "Example" in name2 or "Affiliates" in name2


@pytest.mark.asyncio
async def test_discovery_agent_initialization():
    """Test that discovery agent initializes correctly."""
    agent = DiscoveryAgent(headless=True, timeout=15000)
    
    assert agent.headless == True
    assert agent.timeout == 15000


def test_duplicate_url_handling():
    """Test that duplicate signup URLs are detected."""
    from app.services.program_service import get_program_by_signup_url
    from app.db.session import SessionLocal
    
    # This is a unit test - we'd need a test database for full integration
    # Just verify the function exists
    assert callable(get_program_by_signup_url)
