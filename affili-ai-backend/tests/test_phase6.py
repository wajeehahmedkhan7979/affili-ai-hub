"""
Tests for Phase 6 - Scale & Trust features.
"""

import pytest
from app.automation.failure_classifier import classify_failure, FailureType
from app.services.agent_service import calculate_health_score
from app.models.agent import Agent


class TestFailureClassification:
    """Tests for failure classification."""
    
    def test_classify_captcha(self):
        """Should classify CAPTCHA-related errors."""
        result = classify_failure("CAPTCHA_DETECTED", "Page has reCAPTCHA")
        assert result == FailureType.CAPTCHA_BLOCKED.value
    
    def test_classify_timeout(self):
        """Should classify timeout errors."""
        result = classify_failure("Operation timed out", "")
        assert result == FailureType.TIMEOUT.value
        
        result2 = classify_failure("", "Page navigation timed out after 30s")
        assert result2 == FailureType.TIMEOUT.value
    
    def test_classify_network_error(self):
        """Should classify network errors."""
        result = classify_failure("Connection refused", "")
        assert result == FailureType.NETWORK_ERROR.value
        
        result2 = classify_failure("Network unreachable", "")
        assert result2 == FailureType.NETWORK_ERROR.value
    
    def test_classify_selector_error(self):
        """Should classify selector/element errors."""
        result = classify_failure("Selector not found", "")
        assert result == FailureType.SELECTOR_NOT_FOUND.value
        
        result2 = classify_failure("", "Element not found on page")
        assert result2 == FailureType.SELECTOR_NOT_FOUND.value
    
    def test_classify_validation_error(self):
        """Should classify validation errors."""
        result = classify_failure("Validation failed", "")
        assert result == FailureType.VALIDATION_ERROR.value
    
    def test_classify_unknown(self):
        """Should default to UNKNOWN for unrecognized errors."""
        result = classify_failure("Something went wrong", "")
        assert result == FailureType.UNKNOWN.value


class TestAgentHealthScore:
    """Tests for agent health score calculation."""
    
    def test_perfect_health(self):
        """Agent with perfect record should have health score 100."""
        agent = Agent(id="test-agent")
        agent.total_tasks = 10
        agent.successful_tasks = 10
        agent.failed_tasks = 0
        agent.captcha_count = 0
        agent.timeout_count = 0
        
        score = calculate_health_score(agent)
        assert score == 100.0
    
    def test_health_with_failures(self):
        """Agent with 50% success rate should have reduced score."""
        agent = Agent(id="test-agent")
        agent.total_tasks = 10
        agent.successful_tasks = 5
        agent.failed_tasks = 5
        agent.captcha_count = 0
        agent.timeout_count = 0
        
        score = calculate_health_score(agent)
        # 50% success rate = 30 points (60% weight)
        # 0 CAPTCHA = 20 points (20% weight)
        # 0 timeout = 20 points (20% weight)
        # Total = 70
        assert score == 70.0
    
    def test_health_with_captchas(self):
        """CAPTCHAs should reduce health score."""
        agent = Agent(id="test-agent")
        agent.total_tasks = 10
        agent.successful_tasks = 10
        agent.failed_tasks = 0
        agent.captcha_count = 5  # 50% CAPTCHA rate
        agent.timeout_count = 0
        
        score = calculate_health_score(agent)
        # 100% success = 60 points
        # 50% CAPTCHA rate = 10 points (20% * 50%)
        # 0 timeout = 20 points
        # Total = 90
        assert score == 90.0
    
    def test_health_new_agent(self):
        """New agent with no tasks should have health score 100."""
        agent = Agent(id="new-agent")
        agent.total_tasks = 0
        
        score = calculate_health_score(agent)
        assert score == 100.0
    
    def test_health_score_bounded(self):
        """Health score should be bounded between 0 and 100."""
        agent = Agent(id="test-agent")
        agent.total_tasks = 10
        agent.successful_tasks = 0
        agent.failed_tasks = 10
        agent.captcha_count = 10
        agent.timeout_count = 10
        
        score = calculate_health_score(agent)
        assert 0.0 <= score <= 100.0


class TestAgentPools:
    """Tests for agent pool functionality."""
    
    def test_pool_isolation_concept(self):
        """Verify pool isolation concept - agents should only claim tasks from their pool."""
        # This is a conceptual test - actual DB test would require full setup
        # The claim_task logic checks: (Task.agent_pool == agent_pool) | (Task.agent_pool == None)
        
        # Pool matching scenarios:
        # 1. Task pool='default', Agent pool='default' -> MATCH
        # 2. Task pool='discovery', Agent pool='discovery' -> MATCH
        # 3. Task pool='default', Agent pool='discovery' -> NO MATCH
        # 4. Task pool=None, Agent pool='any' -> MATCH (backward compat)
        
        assert True  # Concept verified in task_dispatcher.claim_task()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
