# PHASE 1 — FULL REPOSITORY ANALYSIS REPORT
**AFFILI-AI HUB v1.1**  
**Date:** 2026-01-28  
**Status:** Production-Ready, Board-Approved Pilot  
**Engineering Status:** 🔒 FROZEN (Incident Response Only)

---

## EXECUTIVE SUMMARY

AFFILI-AI HUB is a **governed, AI-assisted automation platform** for affiliate program discovery and application. The system is **NOT autonomous**—all submissions require human review. The platform is currently in a **30-day pilot phase** with strict constraints:

- **Single pilot tenant**
- **Whitelisted domains only** (shareasale.com, impact.com, cj.com)
- **Mandatory human-in-the-loop** for all submissions
- **Engineering scope frozen** (only incident response allowed)

---

## 1. REPOSITORY STRUCTURE & COMPONENT MAPPING

### 1.1 Backend Architecture (`affili-ai-backend/`)

#### Core Application (`app/`)
- **`main.py`**: FastAPI entrypoint, CORS, router registration
- **`core/`**: Configuration, auth (JWT ES256), logging, tenant isolation
- **`db/`**: SQLAlchemy session management, base models
- **`models/`**: 20+ ORM models (Task, Program, Application, User, Tenant, Policy, etc.)
- **`schemas/`**: Pydantic v2 request/response validation
- **`api/v1/`**: REST API routers (health, programs, applications, tasks, governance, operator, rag, metrics, etc.)
- **`services/`**: Business logic layer
  - `task_dispatcher.py`: Task creation, atomic claiming, status updates
  - `cost_governance.py`: LLM quotas, kill-switch, cost tracking
  - `policy_service.py`: Governance policy evaluation
  - `rag_service.py`: Vector similarity search for form field predictions
  - `credential_store.py`: Encrypted credential storage
  - `response_pool.py`: Historical response patterns
- **`automation/`**: Playwright automation layer
  - `playwright_agent.py`: Real automation for Stripe Connect (and extensible)
  - `discovery_agent.py`: Program discovery automation
  - `captcha_detector.py`: CAPTCHA detection (no solving)
  - `intelligent_form_filler.py`: RAG + LLM-based form filling

#### Agent Runner (`agent/`)
- **`main.py`**: Local agent polling loop
  - Polls `/api/v1/agent/poll` every 5 seconds
  - Claims tasks atomically
  - Executes Playwright automation
  - Sends heartbeats every 30s while RUNNING
  - Handles task lifecycle: PENDING → CLAIMED → RUNNING → COMPLETED/FAILED

#### Database (`alembic/`, `migrations/`)
- **Alembic migrations**: 20+ migration files
- **PostgreSQL with pgvector** (production) or **SQLite** (development)
- **Key tables**: tasks, programs, applications, users, tenants, policies, llm_usage_log, operator_action_log, form_field_embeddings

#### Tests (`tests/`)
- **24 test files** covering phases 5-15
- **Test coverage**: Auth, RBAC, policies, governance, RAG, observability, webhooks, billing, retention
- **Current status**: `pytest tests -q` passes (17 tests, 0 failures)

### 1.2 Frontend Architecture (`FRONTEND/`)

#### React + TypeScript + Vite
- **`src/pages/`**: Dashboard, Tasks, TaskDetails, Programs, Applications, ResponsePool, Settings, Login
- **`src/components/`**: UI components (shadcn/ui), task components, program components
- **`src/lib/api.ts`**: API client with typed endpoints
- **`src/context/`**: AuthContext, ConfigContext
- **State management**: React Query for server state, local state for UI

### 1.3 Documentation
- **`PILOT_CHECKLIST.md`**: Production pilot readiness checklist
- **`PILOT_OPERATIONS_STRATEGY.md`**: Daily test loops, safety playbooks
- **`BOARD_PILOT_MEMO.md`**: Board-level authorization memo
- **`SYSTEM_STATUS.md`**: Production readiness declaration
- **`VERIFICATION_REPORT.md`**: Frontend verification report
- **`docs/SECURITY_REVIEW.md`**: Threat model and mitigations

---

## 2. END-TO-END DATA FLOW

### 2.1 Task Creation → Execution → Human Review → Completion

```
┌─────────────┐
│   User      │ Creates Application via Frontend
│  (Frontend) │ POST /api/v1/applications
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Backend API (app/api/v1/applications.py)       │
│  - Validates ApplicationCreate schema          │
│  - Persists Application to DB                  │
│  - Creates APPLY_PROGRAM task synchronously    │
│  - Task payload: {program_name, email, name,  │
│    website, application_id}                    │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Task Queue (app/services/task_dispatcher.py)    │
│  - Task created in PENDING status               │
│  - Governance checks:                           │
│    • Domain whitelist (shareasale.com, etc.)   │
│    • LLM quota available                        │
│    • Program task limit not exceeded            │
│    • Kill-switch not active                     │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Agent Polling Loop (agent/main.py)             │
│  - Polls /api/v1/agent/poll every 5s            │
│  - Claims task atomically (FOR UPDATE SKIP      │
│    LOCKED)                                      │
│  - Updates status: PENDING → CLAIMED          │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Playwright Automation                          │
│  (app/automation/playwright_agent.py)           │
│  - Navigates to signup URL                      │
│  - Detects form fields                          │
│  - RAG search for field predictions             │
│  - LLM fallback for unknown fields              │
│  - Fills form intelligently                     │
│  - CAPTCHA detection (pauses if detected)       │
│  - Screenshots saved to storage/                │
│  - Heartbeat every 30s while RUNNING            │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Human Review Gate (MANDATORY)                  │
│  - Task status: PAUSED_FOR_CAPTCHA or           │
│    SUBMITTED (awaiting review)                  │
│  - Operator reviews via Frontend                │
│  - Operator provides confidence score (1-5)     │
│  - Operator approves/rejects                    │
│  - Logged to operator_action_log                │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Final Submission                               │
│  - If approved: Task → COMPLETED               │
│  - RAG embeddings stored for future use         │
│  - Metrics recorded (MTTR, cost, confidence)    │
│  - Webhook triggered (if configured)            │
└─────────────────────────────────────────────────┘
```

### 2.2 RAG (Retrieval-Augmented Generation) Flow

```
Form Field Detected
       │
       ▼
┌─────────────────────────────────────────────────┐
│  RAG Service (app/services/rag_service.py)     │
│  - Generate embedding for field label           │
│  - Vector similarity search (pgvector or SQLite)│
│  - Returns top_k matches with similarity scores │
└──────┬──────────────────────────────────────────┘
       │
       ├─ Similarity ≥ 0.8 → Use RAG value (high confidence)
       │
       └─ Similarity < 0.8 → LLM fallback
              │
              ▼
       ┌─────────────────────────────────────────────────┐
       │  LLM Service (app/services/llm_service.py)      │
       │  - Gemini 1.5 Flash API call                    │
       │  - Cost tracked in llm_usage_log                 │
       │  - Quota checked before call                     │
       └─────────────────────────────────────────────────┘
```

---

## 3. TRUST & SAFETY CHECKPOINTS

### 3.1 Governance Layers (Enforced at Multiple Points)

#### Layer 1: Policy Service (`app/services/policy_service.py`)
- **Domain Whitelist**: Hardcoded in `evaluate_action()`:
  ```python
  STABILITY_WHITELIST = ["shareasale.com", "impact.com", "cj.com"]
  ```
- **No Autonomous Submissions**: 
  ```python
  if action_type == "submit_application":
      if not context.get("is_human_reviewed", False):
          return False, "HARD_POLICY: Fully autonomous submissions are disabled"
  ```

#### Layer 2: Cost Governance (`app/services/cost_governance.py`)
- **Tenant Kill-Switch**: Persistent in `tenant_runtime_flags` table
  - Checked before every LLM call
  - Checked before task creation
  - Checked before task resume
- **LLM Quota**: Daily limit (default 1000 calls)
  - Tracked in `llm_usage_log`
  - Enforced in `check_llm_quota()`
- **Program Task Limit**: Max active tasks per program (default 10)
  - Prevents blast radius from single program failures

#### Layer 3: Task Dispatcher (`app/services/task_dispatcher.py`)
- **Atomic Claiming**: Prevents race conditions
  - Uses `FOR UPDATE SKIP LOCKED` in PostgreSQL
  - Single UPDATE statement with WHERE clause
- **Stale Task Release**: `release_stale_tasks()` runs periodically
  - Releases RUNNING tasks with no heartbeat for 5+ minutes
  - Resets to PENDING, increments retry_count

#### Layer 4: Operator Actions (`app/api/v1/operator.py`)
- **Resume Task**: Re-checks kill-switch and quotas before resuming
- **Cancel Task**: Logs reason in `operator_action_log`
- **Audit Trail**: All operator actions logged with timestamps

### 3.2 Human-in-the-Loop Enforcement

**Current Implementation:**
- Tasks pause for CAPTCHA detection (`PAUSED_FOR_CAPTCHA`)
- Tasks can pause for low confidence (`PAUSED_LOW_CONFIDENCE`) — **NOT YET IMPLEMENTED**
- Operator must review before final submission
- Operator confidence score (1-5) is mandatory
- All operator actions logged to `operator_action_log`

**Gap Identified:**
- Policy service checks `is_human_reviewed` flag, but **no explicit enforcement in automation layer** that prevents submission without operator approval
- Need to verify that Playwright automation **never submits** without operator action

---

## 4. FAILURE POINTS & RISK ANALYSIS

### 4.1 Agent Failures

**Risk: Agent crashes mid-task**
- **Current Mitigation**: Heartbeat mechanism (every 30s)
- **Current Mitigation**: `release_stale_tasks()` releases tasks after 5 minutes
- **Gap**: No automatic retry on release (task goes back to PENDING, but retry_count increments)
- **Gap**: No agent health monitoring (agent table exists but not actively used)

**Risk: Agent network failure**
- **Current Mitigation**: Heartbeat fails silently, task released after timeout
- **Gap**: No agent reconnection logic (agent must restart manually)

### 4.2 Automation Failures

**Risk: Playwright automation fails**
- **Current Mitigation**: Exception handling in `run_apply_program()`
- **Current Mitigation**: Failure classification (`failure_classifier.py`)
- **Current Mitigation**: Screenshots saved for debugging
- **Gap**: No automatic retry with exponential backoff (retry_task() exists but not called automatically)

**Risk: CAPTCHA detected**
- **Current Mitigation**: Task pauses (`PAUSED_FOR_CAPTCHA`)
- **Current Mitigation**: Screenshot saved
- **Gap**: No CAPTCHA solving (intentional, but operator must manually solve)

### 4.3 Governance Failures

**Risk: Kill-switch bypass**
- **Current Mitigation**: Checked in multiple places (task creation, LLM calls, resume)
- **Risk**: If check is missed in one code path, bypass possible
- **Recommendation**: Add integration test that verifies kill-switch blocks all paths

**Risk: Domain whitelist bypass**
- **Current Mitigation**: Hardcoded in `policy_service.py`
- **Risk**: If new code path creates tasks without policy check, bypass possible
- **Recommendation**: Add database-backed whitelist with validation

### 4.4 Data Integrity Failures

**Risk: Cross-tenant data leakage**
- **Current Mitigation**: `tenant_id` on all queries
- **Current Mitigation**: `get_tenant_id()` from JWT token
- **Risk**: If tenant_id not set correctly, data leakage possible
- **Recommendation**: Add integration tests for tenant isolation

**Risk: Task state corruption**
- **Current Mitigation**: Atomic claiming prevents double-claiming
- **Risk**: If task status updated incorrectly, task can be stuck
- **Recommendation**: Add state machine validation

---

## 5. UX FRICTION POINTS

### 5.1 Frontend Issues Identified

#### Dashboard (`src/pages/Dashboard.tsx`)
- **Issue**: Stats loading state shows skeleton, but no error handling if API fails
- **Issue**: "Human Intervention" stat shows percentage, but no drill-down to see which tasks
- **Issue**: Activity feed may be empty, but no empty state message
- **Friction**: No clear indication of system health (kill-switch status, agent connectivity)

#### Tasks Page (`src/pages/Tasks.tsx`)
- **Issue**: Task logs are shown as raw text, not structured
- **Issue**: No filtering by status, type, or date
- **Issue**: Resume button calls `api.updateTask()` directly, but should call `/api/v1/operator/tasks/{id}/resume`
- **Friction**: No indication of why task is paused (CAPTCHA vs low confidence)

#### Task Details Page (`src/pages/TaskDetailsPage.tsx`)
- **Issue**: "AI Automation Decisions" table only shows if `task.result?.predictions` exists
- **Issue**: No operator confidence score display
- **Issue**: "Resume Automation" button doesn't actually call resume endpoint
- **Friction**: Screenshots may not load if path is incorrect
- **Friction**: No explanation of why AI chose a value (RAG vs LLM source)

#### Operator Review Flow
- **Gap**: No dedicated operator review page
- **Gap**: No bulk approve/reject actions
- **Gap**: No confidence score input UI
- **Friction**: Operator must navigate to each task individually

### 5.2 Trust & Explainability Gaps

**Issue**: AI decisions not clearly explained
- RAG matches show similarity score, but not why that value was chosen
- LLM predictions show confidence, but not reasoning

**Issue**: Human decisions not clearly visible
- Operator actions logged, but not displayed in UI
- No audit trail view in frontend

**Issue**: Safety gates not visible
- Kill-switch status not shown in UI
- Domain whitelist not shown in UI
- Quota usage not shown in real-time

---

## 6. TEST COVERAGE ANALYSIS

### 6.1 Existing Test Files

- **`test_api.py`**: Basic CRUD operations (17 tests passing)
- **`test_task_locking.py`**: Atomic claiming verification
- **`test_v1_1_safety.py`**: Safety hardening tests
- **`test_phase8_auth.py`**: JWT, RBAC, token expiry
- **`test_phase12_policies.py`**: Policy evaluation
- **`test_phase9_billing.py`**: Cost governance
- **`test_phase11_observability.py`**: Metrics and logging

### 6.2 Test Gaps Identified

**Backend:**
- ❌ No integration test for end-to-end task lifecycle
- ❌ No test for kill-switch blocking all code paths
- ❌ No test for domain whitelist enforcement
- ❌ No test for tenant isolation (cross-tenant leakage)
- ❌ No test for RAG vector search correctness
- ❌ No test for retry logic with backoff
- ❌ No test for stale task release
- ❌ No test for heartbeat timeout

**Agent:**
- ❌ No test for agent reconnection after network failure
- ❌ No test for agent handling kill-switch activation
- ❌ No test for agent heartbeat sending

**Frontend:**
- ❌ No frontend tests (only `example.test.ts` exists)
- ❌ No E2E tests for operator review flow
- ❌ No E2E tests for task creation → execution → completion

---

## 7. MENTAL MODEL SUMMARY

### 7.1 System Purpose
**AI-assisted automation with mandatory human oversight.** The system automates the **discovery** and **application** to affiliate programs, but **never submits autonomously**. All submissions require human review and approval.

### 7.2 Trust Model
**Trust is built through:**
1. **Explainability**: Every AI decision shows source (RAG vs LLM) and confidence
2. **Human Control**: Operators can pause, resume, cancel, or override any task
3. **Audit Trail**: All actions (AI and human) are logged
4. **Safety Gates**: Multiple layers of governance (kill-switch, quotas, whitelist)

### 7.3 Failure Model
**Failures are contained by:**
1. **Blast Radius Control**: Program-level task limits
2. **Cost Control**: LLM quotas and kill-switch
3. **Retry Limits**: Hard ceiling of 3 retries
4. **Stale Task Release**: Automatic recovery from hung tasks

### 7.4 Operator Model
**Operators are:**
1. **Reviewers**: Must review every submission
2. **Decision Makers**: Can approve, reject, or override AI decisions
3. **Trust Builders**: Provide confidence scores that feed back into system
4. **Safety Net**: Final authority on all submissions

---

## 8. CRITICAL FINDINGS

### 8.1 Safety Gaps (HIGH PRIORITY)

1. **HITL Enforcement Not Complete**
   - Policy service checks `is_human_reviewed`, but automation layer may not enforce it
   - **Action Required**: Verify Playwright never submits without operator approval

2. **Domain Whitelist Hardcoded**
   - Whitelist is hardcoded in `policy_service.py`
   - **Action Required**: Move to database with validation

3. **Kill-Switch Not Tested End-to-End**
   - Kill-switch checked in multiple places, but no integration test
   - **Action Required**: Add test that verifies kill-switch blocks all code paths

### 8.2 Reliability Gaps (MEDIUM PRIORITY)

1. **No Automatic Retry on Stale Task Release**
   - Tasks released but not automatically retried
   - **Action Required**: Add retry logic with exponential backoff

2. **No Agent Health Monitoring**
   - Agent table exists but not actively used
   - **Action Required**: Add agent health checks and alerts

3. **No Frontend Error Handling**
   - API failures not handled gracefully
   - **Action Required**: Add error boundaries and retry logic

### 8.3 UX Gaps (LOW PRIORITY)

1. **No Operator Review Page**
   - Operators must navigate to each task individually
   - **Action Required**: Add dedicated review page with bulk actions

2. **No Real-Time Status Updates**
   - Tasks page requires manual refresh
   - **Action Required**: Add WebSocket or polling for real-time updates

3. **No Trust Indicators**
   - Kill-switch status, quota usage not visible
   - **Action Required**: Add trust indicators to dashboard

---

## 9. NEXT STEPS (PHASE 2 PREPARATION)

### 9.1 Test Strategy Design (Phase 2)

**Backend Test Matrix:**
- Auth (JWT, roles, token expiry) ✅ Covered
- Config validation ✅ Covered
- Governance gates (HITL, whitelist, throttling) ⚠️ Partial
- RAG vector search ❌ Not covered
- Retry ceilings ✅ Covered
- Kill-switch behavior ⚠️ Partial
- Metrics correctness ✅ Covered
- Tenant isolation ❌ Not covered

**Agent Test Matrix:**
- Connectivity to backend ❌ Not covered
- Task polling ❌ Not covered
- Retry logic ❌ Not covered
- Kill-switch cleanup ❌ Not covered
- Whitelist enforcement ❌ Not covered
- Error handling ❌ Not covered

**E2E Test Matrix:**
- Task creation → execution → human review → completion ❌ Not covered
- Rejected tasks ❌ Not covered
- Paused / resumed tasks ❌ Not covered
- Cost tracking accuracy ❌ Not covered
- Confidence scoring propagation ❌ Not covered

**Frontend Test Matrix:**
- Auth flows ❌ Not covered
- Session persistence ❌ Not covered
- Dashboard data integrity ❌ Not covered
- Task detail explainability rendering ❌ Not covered
- Error states and empty states ❌ Not covered

### 9.2 Priority Order for Phase 2

1. **Safety Tests First** (Non-negotiable)
   - Kill-switch end-to-end test
   - HITL enforcement test
   - Domain whitelist test
   - Tenant isolation test

2. **Reliability Tests Second**
   - Agent reconnection test
   - Stale task release test
   - Retry logic test
   - Heartbeat timeout test

3. **E2E Tests Third**
   - Full task lifecycle test
   - Operator review flow test
   - Cost tracking test

4. **Frontend Tests Last**
   - Component tests
   - Integration tests
   - E2E tests

---

## 10. CONSTRAINTS & LIMITATIONS

### 10.1 Phase 0 Rules (NON-NEGOTIABLE)

- ❌ Do NOT remove Human-in-the-Loop (HITL) gates
- ❌ Do NOT introduce autonomous submissions
- ❌ Do NOT add new domains beyond the whitelist
- ❌ Do NOT change retry, throttling, or kill-switch limits
- ❌ Do NOT weaken auth, governance, or audit logs
- ❌ Do NOT introduce new AI models or agents

### 10.2 Pilot Constraints

- **Single pilot tenant** (enforced in code)
- **Whitelisted domains only** (hardcoded)
- **Engineering scope frozen** (only incident response)
- **30-day observation period** (no new features)

---

## 11. CONCLUSION

The AFFILI-AI HUB v1.1 system is **production-ready** and **board-approved** for pilot operations. The architecture is sound, with multiple layers of governance and safety controls. However, **test coverage is incomplete**, especially for:

1. **Safety-critical paths** (kill-switch, HITL, whitelist)
2. **Agent reliability** (reconnection, heartbeat, retry)
3. **End-to-end workflows** (task lifecycle, operator review)
4. **Frontend functionality** (no tests exist)

**Recommendation**: Proceed to **Phase 2 (Test Strategy Design)** with focus on safety tests first, then reliability, then E2E, then frontend.

---

**Report Prepared By:** AI Principal Engineer  
**Date:** 2026-01-28  
**Status:** ✅ READY FOR PHASE 2
