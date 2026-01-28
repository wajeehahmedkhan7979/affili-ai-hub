"""
Tests for atomic task claim behavior.
"""

import uuid

from app.models.task import TaskType, TaskStatus
from app.services.task_dispatcher import create_task, claim_task


def test_atomic_claim_allows_only_single_winner(db_session):
    """Ensure that only one agent can claim a pending task.

    The service uses a single UPDATE ... WHERE status='PENDING' statement.
    This test verifies that a second claim attempt returns None once the
    first claim has succeeded.
    """
    # Create a pending task
    task = create_task(
        db_session,
        TaskType.DISCOVER_PROGRAM,
        {"url": "https://example.com"},
    )

    # First agent successfully claims the task
    first_claim = claim_task(db_session, task.id, "agent-1")
    assert first_claim is not None
    assert first_claim.status == TaskStatus.CLAIMED
    assert first_claim.agent_id == "agent-1"

    # Second agent should fail to claim the same task
    second_claim = claim_task(db_session, task.id, "agent-2")
    assert second_claim is None

