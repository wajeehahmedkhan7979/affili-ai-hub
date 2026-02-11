# PHASE 2 — TEST STRATEGY DESIGN
**AFFILI-AI HUB v1.1 (Frozen Baseline)**  
**Purpose:** Prove safety, reliability, and operator trust — not add behavior  
**Date:** 2026-01-28  
**Status:** 🔒 EXECUTION READY

---

## PHASE 2 OBJECTIVE

Convert the implicit guarantees of v1.1 into explicit, repeatable, automated proof.

**This phase answers one question only:**

> "If this system fails, will it fail safely, observably, and recoverably?"

---

## 1. TESTING PRINCIPLES (NON-NEGOTIABLE)

### 1.1 No Behavior Changes
- Tests may expose bugs
- Fixes allowed **only if they restore intended documented behavior**
- No new features, no enhancements, no optimizations

### 1.2 Black-Box First
- Prefer API-level and integration tests over unit tests
- Test outcomes, not implementation details
- Use real database (test schema), mock external services

### 1.3 Safety Before Correctness
- A test that proves a kill-switch blocks execution is **more valuable** than a test proving a happy path works
- Layer 1 failures = **STOP PILOT**

### 1.4 Deterministic
- No flaky timing (use time mocking)
- No real LLM calls (mock Gemini API)
- No external network dependency unless explicitly required (mock Playwright)

---

## 2. TEST LAYERING MODEL

```
┌───────────────────────────────┐
│  Layer 4: Frontend E2E        │  (Playwright / Cypress)
├───────────────────────────────┤
│  Layer 3: Full E2E (API+Agent)│  (pytest + agent harness)
├───────────────────────────────┤
│  Layer 2: Integration Tests   │  (pytest, real DB)
├───────────────────────────────┤
│  Layer 1: Safety Invariants   │  (pytest, must NEVER fail)
└───────────────────────────────┘
```

**Execution Order:** Layer 1 → Layer 2 → Layer 3 → Layer 4  
**If Layer 1 fails → STOP**

---

## 3. LAYER 1 — SAFETY INVARIANT TESTS (HIGHEST PRIORITY)

**These tests assert things that must never be violated.**

### 3.1 Kill-Switch Global Enforcement Test

**Goal:** Prove that every execution path halts when kill-switch is active.

**Test File:** `tests/test_layer1_killswitch.py`

#### Test Cases:

**TC-1.1: Task Creation Blocked**
```python
def test_killswitch_blocks_task_creation():
    """Creating a task while kill-switch is ON → ❌ blocked"""
    # Setup: Enable kill-switch for tenant
    # Action: POST /api/v1/tasks
    # Assert: HTTP 403, explicit error message
    # Assert: No task created in DB
```

**TC-1.2: Task Polling Blocked**
```python
def test_killswitch_blocks_task_polling():
    """Polling a task while kill-switch is ON → ❌ blocked"""
    # Setup: Enable kill-switch, create task
    # Action: POST /api/v1/agent/poll
    # Assert: HTTP 403 or empty task list
    # Assert: Task remains PENDING
```

**TC-1.3: Task Resume Blocked**
```python
def test_killswitch_blocks_task_resume():
    """Resuming a paused task while kill-switch is ON → ❌ blocked"""
    # Setup: Enable kill-switch, create paused task
    # Action: POST /api/v1/operator/tasks/{id}/resume
    # Assert: HTTP 403
    # Assert: Task remains paused
```

**TC-1.4: LLM Call Blocked**
```python
def test_killswitch_blocks_llm_call():
    """LLM call while kill-switch is ON → ❌ blocked"""
    # Setup: Enable kill-switch
    # Action: Attempt LLM call via automation
    # Assert: check_llm_allowed() returns {"allowed": False}
    # Assert: No LLM API call made
```

**Implementation Notes:**
- Use `cost_governance.enable_tenant_killswitch()` to activate
- Verify `tenant_runtime_flags.ai_disabled = True` in DB
- Assert HTTP 403 or explicit error message
- Assert no DB side effects (no tasks created, no LLM logs)

---

### 3.2 Human-in-the-Loop (HITL) Hard Gate Test

**Goal:** Prove autonomous submission is impossible.

**Test File:** `tests/test_layer1_hitl.py`

#### Test Cases:

**TC-2.1: Policy Service Blocks Autonomous Submission**
```python
def test_policy_blocks_autonomous_submission():
    """Attempt submission without is_human_reviewed=true → ❌ blocked"""
    # Setup: Create task, attempt submission
    # Action: Call policy_service.evaluate_action("submit_application", {...})
    # Assert: Returns (False, "HARD_POLICY: Fully autonomous submissions are disabled")
```

**TC-2.2: Automation Path Blocks Submission**
```python
def test_automation_blocks_autonomous_submission():
    """Attempt submission via automation path → ❌ blocked"""
    # Setup: Mock Playwright automation
    # Action: Attempt form submission without operator approval
    # Assert: Task pauses or fails
    # Assert: No actual submission occurs
```

**TC-2.3: Direct API Call Blocks Submission**
```python
def test_api_blocks_autonomous_submission():
    """Attempt submission via direct API call → ❌ blocked"""
    # Setup: Create task
    # Action: POST /api/v1/tasks/{id}/submit (if exists) without operator approval
    # Assert: HTTP 403 or 400
    # Assert: Task remains in paused/submitted state
```

**Expected Results:**
- ❌ Hard failure with policy reason
- ✅ Task remains paused / incomplete
- ✅ Operator action required
- ✅ Audit log entry created

**This test protects you legally.**

---

### 3.3 Domain Whitelist Enforcement Test

**Goal:** Prove automation cannot target non-approved domains.

**Test File:** `tests/test_layer1_whitelist.py`

#### Test Cases:

**TC-3.1: Non-Whitelisted Domain Rejected**
```python
def test_whitelist_blocks_example_com():
    """Create task for example.com → ❌ rejected"""
    # Setup: Create task with program_domain="example.com"
    # Action: POST /api/v1/tasks with APPLY_PROGRAM type
    # Assert: HTTP 403
    # Assert: Error message contains "disabled for pilot phase stability"
```

**TC-3.2: Whitelisted Domain Allowed**
```python
def test_whitelist_allows_shareasale():
    """Create task for shareasale.com → ✅ allowed"""
    # Setup: Create task with program_domain="shareasale.com"
    # Action: POST /api/v1/tasks
    # Assert: HTTP 201
    # Assert: Task created successfully
```

**TC-3.3: Payload Tampering Blocked**
```python
def test_whitelist_blocks_payload_tampering():
    """Attempt to override domain via payload tampering → ❌ rejected"""
    # Setup: Create program with shareasale.com
    # Action: Create task with payload containing example.com URL
    # Assert: Policy service extracts domain from program, not payload
    # Assert: Task creation blocked if domain mismatch
```

**Whitelist:** `["shareasale.com", "impact.com", "cj.com"]` (hardcoded in `policy_service.py`)

---

### 3.4 Tenant Isolation Test

**Goal:** Prove no cross-tenant data leakage.

**Test File:** `tests/test_layer1_tenant_isolation.py`

#### Test Cases:

**TC-4.1: Tenant A Cannot Read Tenant B Tasks**
```python
def test_tenant_cannot_read_other_tasks():
    """Tenant A cannot read Tenant B tasks"""
    # Setup: Create task for Tenant B
    # Action: Tenant A calls GET /api/v1/tasks
    # Assert: Only Tenant A tasks returned
    # Assert: Tenant B task not in results
```

**TC-4.2: Tenant A Cannot Modify Tenant B Applications**
```python
def test_tenant_cannot_modify_other_applications():
    """Tenant A cannot modify Tenant B applications"""
    # Setup: Create application for Tenant B
    # Action: Tenant A calls PUT /api/v1/applications/{tenant_b_id}
    # Assert: HTTP 404 or 403
    # Assert: Application unchanged
```

**TC-4.3: Forged Tenant ID Rejected**
```python
def test_forged_tenant_id_rejected():
    """JWT with forged tenant_id → ❌ rejected"""
    # Setup: Create JWT token with forged tenant_id
    # Action: Use token to access API
    # Assert: HTTP 401 or 403
    # Assert: Token validation fails
```

**Implementation Notes:**
- Use `get_tenant_id()` from JWT token
- Verify all queries filter by `tenant_id`
- Test with multiple tenants in same DB

---

## 4. LAYER 2 — RELIABILITY & RECOVERY TESTS

**These tests prove the system recovers from expected failures.**

### 4.1 Stale Task Release Test

**Goal:** Hung agents do not brick the system.

**Test File:** `tests/test_layer2_stale_task_release.py`

#### Test Cases:

**TC-5.1: Stale Task Automatically Released**
```python
def test_stale_task_released_after_timeout():
    """Task enters RUNNING, no heartbeat for >5 minutes → released"""
    # Setup: Create task, set status=RUNNING, set started_at=6 minutes ago
    # Action: Call release_stale_tasks(timeout_seconds=300)
    # Assert: Task status = PENDING
    # Assert: agent_id = None
    # Assert: retry_count += 1
    # Assert: Log entry added
```

**TC-5.2: Active Task Not Released**
```python
def test_active_task_not_released():
    """Task with recent heartbeat → not released"""
    # Setup: Create task, set status=RUNNING, set last_heartbeat=1 minute ago
    # Action: Call release_stale_tasks(timeout_seconds=300)
    # Assert: Task status = RUNNING (unchanged)
    # Assert: agent_id unchanged
```

**Implementation Notes:**
- Mock `datetime.utcnow()` to control time
- Use `task_dispatcher.release_stale_tasks()`
- Verify log message appended to task.logs

---

### 4.2 Retry Ceiling Enforcement Test

**Goal:** Prevent infinite retries.

**Test File:** `tests/test_layer2_retry_ceiling.py`

#### Test Cases:

**TC-6.1: Retry Ceiling Enforced**
```python
def test_retry_ceiling_enforced():
    """Force task failure 3 times → fourth attempt blocked"""
    # Setup: Create task with retry_count=3, max_retries=3
    # Action: Call retry_task()
    # Assert: Returns None (no retry)
    # Assert: Task status = FAILED
    # Assert: retry_count = 3 (not incremented)
```

**TC-6.2: Retry Allowed Before Ceiling**
```python
def test_retry_allowed_before_ceiling():
    """Task with retry_count < max_retries → retry allowed"""
    # Setup: Create task with retry_count=1, max_retries=3
    # Action: Call retry_task()
    # Assert: Task status = PENDING
    # Assert: retry_count = 2
```

**Hard Ceiling:** `min(task.max_retries, 3)` (enforced in `task_dispatcher.retry_task()`)

---

### 4.3 Agent Kill-Switch Reaction Test

**Goal:** Agent stops cleanly when governance intervenes.

**Test File:** `tests/test_layer2_agent_killswitch_reaction.py`

#### Test Cases:

**TC-7.1: Agent Halts on Kill-Switch Activation**
```python
def test_agent_halts_on_killswitch():
    """Agent running task, kill-switch activated → agent halts"""
    # Setup: Agent running task, enable kill-switch
    # Action: Agent polls for next task
    # Assert: Agent receives empty task list or 403
    # Assert: Agent stops processing
```

**TC-7.2: Active Task Auto-Canceled**
```python
def test_active_task_canceled_on_killswitch():
    """Kill-switch activated → active task auto-canceled"""
    # Setup: Create RUNNING task, enable kill-switch
    # Action: Call cost_governance.enable_tenant_killswitch()
    # Assert: Task status = FAILED
    # Assert: error_message contains "Tenant Kill-switch Active"
    # Assert: No partial submission
```

**Implementation Notes:**
- Use `cost_governance.cleanup_disabled_tenant_tasks()`
- Verify all active tasks (PENDING, CLAIMED, RUNNING, PAUSED) are canceled
- Assert no partial state changes

---

## 5. LAYER 3 — END-TO-END WORKFLOW TESTS

**These tests validate the actual business workflow.**

### 5.1 Full Happy-Path Lifecycle Test

**Goal:** Verify complete task lifecycle from creation to completion.

**Test File:** `tests/test_layer3_happy_path.py`

#### Workflow:

```
1. Application Created
   ↓
2. Task Created (APPLY_PROGRAM)
   ↓
3. Agent Claims Task
   ↓
4. Automation Runs (mocked Playwright)
   ↓
5. Task Pauses (CAPTCHA detected)
   ↓
6. Operator Reviews
   ↓
7. Operator Approves (confidence score 4/5)
   ↓
8. Task Completes
   ↓
9. Metrics Recorded
```

#### Assertions:

**TC-8.1: State Transitions Correct**
```python
def test_happy_path_state_transitions():
    """Verify correct state transitions"""
    # PENDING → CLAIMED → RUNNING → PAUSED_FOR_CAPTCHA → PENDING → RUNNING → COMPLETED
    # Assert each transition is valid
```

**TC-8.2: Operator Action Logged**
```python
def test_operator_action_logged():
    """Operator approval logged to operator_action_log"""
    # Assert: operator_action_log entry created
    # Assert: action = RESUME_TASK or APPROVE_TASK
    # Assert: operator_id set
    # Assert: timestamp recorded
```

**TC-8.3: Confidence Score Stored**
```python
def test_confidence_score_stored():
    """Operator confidence score stored in task"""
    # Assert: task.operator_confidence = 4
    # Assert: task.feedback_json contains confidence data
```

**TC-8.4: RAG Updated**
```python
def test_rag_updated_on_completion():
    """Successful form submission updates RAG embeddings"""
    # Assert: form_field_embeddings table has new entries
    # Assert: embeddings match submitted values
```

**TC-8.5: Cost Logged**
```python
def test_cost_logged():
    """LLM costs tracked in llm_usage_log"""
    # Assert: llm_usage_log entries created
    # Assert: cost_usd > 0
    # Assert: tokens_used > 0
    # Assert: task_id linked
```

**Implementation Notes:**
- Mock Playwright automation (no real browser)
- Mock LLM API (no real Gemini calls)
- Use test database (SQLite or isolated Postgres schema)
- Verify all assertions in single test or split into subtests

---

### 5.2 Rejection Flow Test

**Goal:** Ensure rejections are clean and auditable.

**Test File:** `tests/test_layer3_rejection_flow.py`

#### Test Cases:

**TC-9.1: Task Stops Permanently on Rejection**
```python
def test_rejection_stops_task():
    """Operator rejects task → task stops permanently"""
    # Setup: Create paused task
    # Action: Operator cancels task with reason
    # Assert: Task status = FAILED_OPERATOR_CANCEL
    # Assert: No retries scheduled
```

**TC-9.2: Audit Log Contains Reason**
```python
def test_rejection_audit_logged():
    """Rejection reason logged to audit log"""
    # Assert: operator_action_log entry created
    # Assert: action = CANCEL_TASK
    # Assert: reason field populated
```

**TC-9.3: UI Reflects Rejected State**
```python
def test_ui_reflects_rejected_state():
    """Frontend shows rejected state correctly"""
    # Action: GET /api/v1/tasks/{id}
    # Assert: status = FAILED_OPERATOR_CANCEL
    # Assert: error_message contains reason
```

---

### 5.3 Cost-Per-Success Test

**Goal:** Verify governance economics.

**Test File:** `tests/test_layer3_cost_tracking.py`

#### Test Cases:

**TC-10.1: LLM Cost Tracked**
```python
def test_llm_cost_tracked():
    """LLM calls tracked in llm_usage_log"""
    # Setup: Make LLM call during automation
    # Assert: llm_usage_log entry created
    # Assert: cost_usd > 0
    # Assert: tokens_used > 0
```

**TC-10.2: Cost Attributed to Task**
```python
def test_cost_attributed_to_task():
    """LLM cost linked to task_id"""
    # Assert: llm_usage_log.task_id matches task.id
    # Assert: Cost can be aggregated per task
```

**TC-10.3: Cost-Per-Success Metric Accurate**
```python
def test_cost_per_success_metric():
    """Cost-per-success calculation is accurate"""
    # Setup: Complete 3 tasks, total cost $0.15
    # Assert: Cost-per-success = $0.05
    # Assert: Metric available via GET /api/v1/metrics
```

---

## 6. LAYER 4 — FRONTEND VERIFICATION (UX + TRUST)

**Frontend tests are trust-preserving, not cosmetic.**

### 6.1 Auth & Session Tests

**Test File:** `tests/frontend/test_auth_session.py`

#### Test Cases:

**TC-11.1: Login Persistence**
```python
def test_login_persistence():
    """User stays logged in after page refresh"""
    # Action: Login, refresh page
    # Assert: User still authenticated
    # Assert: Token valid
```

**TC-11.2: Token Expiry Handling**
```python
def test_token_expiry_handling():
    """Expired token triggers re-login"""
    # Setup: Expire token
    # Action: Make API call
    # Assert: Redirected to login
    # Assert: Error message shown
```

**TC-11.3: Role-Based UI Visibility**
```python
def test_role_based_ui_visibility():
    """UI elements shown based on user role"""
    # Setup: Login as OPERATOR
    # Assert: Admin-only buttons hidden
    # Assert: Operator actions visible
```

---

### 6.2 Trust Signal Visibility Tests

**Goal:** Verify UI shows all safety gates and trust indicators.

**Test File:** `tests/frontend/test_trust_signals.py`

#### Test Cases:

**TC-12.1: Kill-Switch Status Visible**
```python
def test_killswitch_status_visible():
    """Dashboard shows kill-switch status"""
    # Action: Load dashboard
    # Assert: Kill-switch status displayed
    # Assert: Status is clear (ON/OFF)
    # Assert: Reason shown if active
```

**TC-12.2: Agent Connectivity Visible**
```python
def test_agent_connectivity_visible():
    """Dashboard shows agent connectivity"""
    # Action: Load dashboard
    # Assert: Agent status displayed
    # Assert: Last seen timestamp shown
```

**TC-12.3: Task Pause Reason Visible**
```python
def test_task_pause_reason_visible():
    """Task details show why task is paused"""
    # Action: View paused task
    # Assert: Pause reason displayed
    # Assert: CAPTCHA screenshot shown if applicable
```

**TC-12.4: Operator Confidence Score Visible**
```python
def test_confidence_score_visible():
    """Task details show operator confidence score"""
    # Action: View completed task
    # Assert: Confidence score displayed (1-5)
    # Assert: Score is prominent
```

**TC-12.5: AI Decision Source Visible**
```python
def test_ai_decision_source_visible():
    """AI decisions show source (RAG vs LLM)"""
    # Action: View task with AI predictions
    # Assert: Source badge shown (RAG/LLM)
    # Assert: Confidence score shown
    # Assert: Reasoning displayed
```

**If a safety gate exists but isn't visible → UX failure.**

---

### 6.3 Operator Flow Tests

**Test File:** `tests/frontend/test_operator_flow.py`

#### Test Cases:

**TC-13.1: Resume Task Calls Correct Endpoint**
```python
def test_resume_task_calls_correct_endpoint():
    """Resume button calls /api/v1/operator/tasks/{id}/resume"""
    # Action: Click resume button
    # Assert: POST /api/v1/operator/tasks/{id}/resume called
    # Assert: Not POST /api/v1/tasks/{id}/update
```

**TC-13.2: Cancel Task Logs Audit Reason**
```python
def test_cancel_task_logs_reason():
    """Cancel task requires reason and logs it"""
    # Action: Cancel task with reason
    # Assert: Reason sent to API
    # Assert: operator_action_log entry created
```

**TC-13.3: Confidence Input Required**
```python
def test_confidence_input_required():
    """Confidence score required before approval"""
    # Action: Attempt approval without confidence score
    # Assert: Validation error shown
    # Assert: Approval blocked
```

**TC-13.4: Error States Explicit**
```python
def test_error_states_explicit():
    """Error states are explicit and non-silent"""
    # Action: Trigger error (e.g., network failure)
    # Assert: Error message displayed
    # Assert: Error is actionable (retry button, etc.)
```

---

## 7. EXECUTION ORDER (IMPORTANT)

**Run tests in this order — do not parallelize initially:**

1. **Layer 1 — Safety Invariants** (MUST PASS)
   - `test_layer1_killswitch.py`
   - `test_layer1_hitl.py`
   - `test_layer1_whitelist.py`
   - `test_layer1_tenant_isolation.py`

2. **Layer 2 — Reliability** (SHOULD PASS)
   - `test_layer2_stale_task_release.py`
   - `test_layer2_retry_ceiling.py`
   - `test_layer2_agent_killswitch_reaction.py`

3. **Layer 3 — E2E Lifecycle** (SHOULD PASS)
   - `test_layer3_happy_path.py`
   - `test_layer3_rejection_flow.py`
   - `test_layer3_cost_tracking.py`

4. **Layer 4 — Frontend** (SHOULD PASS)
   - `tests/frontend/test_auth_session.py`
   - `tests/frontend/test_trust_signals.py`
   - `tests/frontend/test_operator_flow.py`

**If Layer 1 fails → STOP**

---

## 8. WHAT NOT TO TEST (INTENTIONALLY)

**To respect the freeze:**

- ❌ Performance tuning
- ❌ New automation logic
- ❌ New domains
- ❌ New AI behaviors
- ❌ Visual redesign experiments

**This is verification, not evolution.**

---

## 9. IMPLEMENTATION GUIDELINES

### 9.1 Test Structure

```python
# tests/test_layer1_killswitch.py

import pytest
from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.services.cost_governance import cost_governance
from app.models.task import Task, TaskStatus
import uuid

@pytest.fixture
def test_tenant_id():
    """Fixture for test tenant UUID"""
    return uuid.uuid4()

@pytest.fixture
def test_db():
    """Fixture for test database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestKillSwitchEnforcement:
    """Layer 1: Kill-switch global enforcement tests"""
    
    def test_killswitch_blocks_task_creation(self, test_client, test_tenant_id, test_db):
        """TC-1.1: Creating a task while kill-switch is ON → ❌ blocked"""
        # Setup
        cost_governance.enable_tenant_killswitch(
            db=test_db,
            tenant_id=test_tenant_id,
            reason="Test kill-switch",
            disabled_by=test_tenant_id
        )
        
        # Action
        response = test_client.post(
            "/api/v1/tasks",
            json={
                "task_type": "APPLY_PROGRAM",
                "payload": {"program_name": "Test Program"}
            },
            headers={"X-Tenant-ID": str(test_tenant_id)}
        )
        
        # Assert
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()
        
        # Verify no task created
        task_count = test_db.query(Task).filter(
            Task.tenant_id == test_tenant_id
        ).count()
        assert task_count == 0
```

### 9.2 Mocking Strategy

**LLM Calls:**
```python
@pytest.fixture
def mock_llm_service(monkeypatch):
    """Mock LLM service to avoid real API calls"""
    def mock_generate(prompt):
        return {"text": "mocked response", "tokens": 10, "cost": 0.001}
    
    monkeypatch.setattr("app.services.llm_service.generate", mock_generate)
```

**Playwright:**
```python
@pytest.fixture
def mock_playwright(monkeypatch):
    """Mock Playwright automation"""
    async def mock_run_automation(payload, task_id):
        return {
            "success": True,
            "screenshots": {},
            "logs": "Mocked automation logs"
        }
    
    monkeypatch.setattr(
        "app.automation.playwright_agent.run_apply_program_automation",
        mock_run_automation
    )
```

**Time:**
```python
from unittest.mock import patch
from datetime import datetime, timedelta

@patch("app.services.task_dispatcher.datetime")
def test_stale_task_release(mock_datetime):
    """Test stale task release with mocked time"""
    # Set current time
    mock_datetime.utcnow.return_value = datetime.utcnow()
    
    # Create task with old timestamp
    task.started_at = datetime.utcnow() - timedelta(minutes=6)
    
    # Run release
    release_stale_tasks(timeout_seconds=300)
    
    # Assert task released
```

### 9.3 Test Database Setup

```python
# tests/conftest.py

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    from app.db.session import engine
    from app.db.base import Base
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db(test_db_engine):
    """Create test database session"""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()
```

---

## 10. DELIVERABLES OF PHASE 2

**At completion you should have:**

1. ✅ **A green test suite**
   - All Layer 1 tests passing
   - All Layer 2 tests passing
   - All Layer 3 tests passing
   - All Layer 4 tests passing

2. ✅ **A written safety assurance summary**
   - Document confirming all safety invariants verified
   - List of confirmed invariants
   - Short list of accepted known risks

3. ✅ **High confidence the pilot can survive real-world variance**
   - Tests prove system fails safely
   - Tests prove system recovers from failures
   - Tests prove operator trust is preserved

---

## 11. EXECUTION CHECKLIST

### Phase 2.1: Layer 1 Implementation
- [ ] Create `tests/test_layer1_killswitch.py`
- [ ] Create `tests/test_layer1_hitl.py`
- [ ] Create `tests/test_layer1_whitelist.py`
- [ ] Create `tests/test_layer1_tenant_isolation.py`
- [ ] Run Layer 1 tests: `pytest tests/test_layer1_*.py -v`
- [ ] Fix any failures (only restore intended behavior)
- [ ] Document results

### Phase 2.2: Layer 2 Implementation
- [ ] Create `tests/test_layer2_stale_task_release.py`
- [ ] Create `tests/test_layer2_retry_ceiling.py`
- [ ] Create `tests/test_layer2_agent_killswitch_reaction.py`
- [ ] Run Layer 2 tests: `pytest tests/test_layer2_*.py -v`
- [ ] Fix any failures
- [ ] Document results

### Phase 2.3: Layer 3 Implementation
- [ ] Create `tests/test_layer3_happy_path.py`
- [ ] Create `tests/test_layer3_rejection_flow.py`
- [ ] Create `tests/test_layer3_cost_tracking.py`
- [ ] Run Layer 3 tests: `pytest tests/test_layer3_*.py -v`
- [ ] Fix any failures
- [ ] Document results

### Phase 2.4: Layer 4 Implementation
- [ ] Create `tests/frontend/test_auth_session.py`
- [ ] Create `tests/frontend/test_trust_signals.py`
- [ ] Create `tests/frontend/test_operator_flow.py`
- [ ] Run Layer 4 tests: `pytest tests/frontend/ -v`
- [ ] Fix any failures
- [ ] Document results

### Phase 2.5: Final Verification
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Generate coverage report: `pytest --cov=app tests/`
- [ ] Write safety assurance summary
- [ ] Document known risks

---

## 12. SUCCESS CRITERIA

**Phase 2 is successful when:**

1. ✅ All Layer 1 tests pass (100% required)
2. ✅ All Layer 2 tests pass (95%+ required)
3. ✅ All Layer 3 tests pass (90%+ required)
4. ✅ All Layer 4 tests pass (85%+ required)
5. ✅ Safety assurance summary written
6. ✅ Known risks documented
7. ✅ Test suite is deterministic (no flaky tests)

**If Layer 1 fails → STOP PILOT**

---

## FINAL DIRECTION

**You are now at the most dangerous and most valuable phase of the project.**

- **Design discipline > speed**
- **Proof > belief**
- **Safety > capability**

**This test strategy is your safety net. Execute it methodically, verify each layer before proceeding, and never compromise on Layer 1.**

---

**Status:** ✅ READY FOR EXECUTION  
**Next Step:** Begin Phase 2.1 — Layer 1 Implementation
