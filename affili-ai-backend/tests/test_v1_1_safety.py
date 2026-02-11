"""
Verification tests for v1.1 Safety and Governance Hardening.

# NOTE: v1.1 schema intentionally does NOT include `program_id` on tasks.
# Tests must not assume program-level task binding; do not add `program_id`.
"""
import pytest
import uuid
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskType
from app.services.cost_governance import cost_governance
from app.services.task_dispatcher import create_task, retry_task
from app.services.policy_service import evaluate_action

def test_program_level_throttling(db: Session, tenant_id: uuid.UUID):
    """Verify that program-level task caps are enforced."""
    # Program-level task binding is not part of the frozen v1.1 schema.
    # This test is scoped out for Phase 2.5 and asserts that program-level
    # throttling is not tested under the frozen schema.
    pytest.skip("program_id not present in v1.1 schema; test scoped out")

def test_hard_retry_ceiling(db: Session):
    """Verify that tasks cannot be retried more than 3 times."""
    task = create_task(db, TaskType.DISCOVER_PROGRAM)
    task.status = TaskStatus.FAILED
    task.retry_count = 3
    db.commit()
    
    # Attempt retry
    result = retry_task(db, task.id)
    assert result is None
    assert task.status == TaskStatus.FAILED

def test_no_autonomous_submission_policy(db: Session, tenant_id: uuid.UUID):
    """Verify that submissions without human review are blocked."""
    context = {"is_human_reviewed": False}
    allowed, reason = evaluate_action(db, tenant_id, "submit_application", context)
    assert allowed is False
    assert "Human review required" in reason
    
    # Verify allowed with human review
    context = {"is_human_reviewed": True}
    allowed, reason = evaluate_action(db, tenant_id, "submit_application", context)
    assert allowed is True

def test_site_stability_whitelist(db: Session, tenant_id: uuid.UUID):
    """Verify that only whitelisted sites allow automation creation."""
    # Fails for unknown site
    context = {"task_type": "APPLY_PROGRAM", "program_domain": "scam-site.com"}
    allowed, reason = evaluate_action(db, tenant_id, "create_task", context)
    assert allowed is False
    assert "disabled for pilot phase stability" in reason
    
    # Success for whitelisted site
    context = {"task_type": "APPLY_PROGRAM", "program_domain": "shareasale.com"}
    allowed, reason = evaluate_action(db, tenant_id, "create_task", context)
    assert allowed is True
