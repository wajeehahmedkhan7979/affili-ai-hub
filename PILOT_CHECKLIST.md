# 🚀 AFFILI-AI HUB: Production Pilot Checklist (v1.0.0)

This checklist follows the successful stabilization of the v1.1.0 codebase. It is designed to guide a CTO or Lead Engineer through the first 30 days of live pilot operations.

> [!IMPORTANT]
> **Pilot Operations Strategy**: Refer to [PILOT_OPERATIONS_STRATEGY.md](file:///d:/PROJECTS-REPOS/AFFILIATE-PROJ/affili-ai-hub/PILOT_OPERATIONS_STRATEGY.md) for the mandatory daily test loops and safety incident playbooks.

## 1. Zero-Trust Infrastructure Readiness 🔐
- [ ] **Secret Rotation**: Rotate the default `SECRET_KEY` and `GEMINI_API_KEY` away from development values.
- [ ] **Database Hardening**: Ensure the Supabase/PostgreSQL connection string is restricted to the backend IP range.
- [ ] **VPC Isolation**: Confirm the Playwright Workers are running in a subnet that can only access the Backend API and the Public Internet (no local network exposure).
- [ ] **JWT Policy**: Verify that `ACCESS_TOKEN_EXPIRE_MINUTES` is set to ≤ 30 for production.

## 2. Operational Governance Setup 📉
- [ ] **Cost Limits**: Set the initial `USD` quota in `tenant_runtime_flags` for the first pilot tenant.
- [ ] **Audit Trail Baseline**: Run a test 'RESUME_TASK' and 'CANCEL_TASK' to verify the `operator_action_log` is capturing human decisions.
- [ ] **Prometheus Alerting**: Configure alerts for `mttr_seconds > 1800` (30 mins) to catch agent hanging issues early.

## 3. Deployment Dry Run (The "Staging" Pass) 🏗️
- [ ] **Cloud Migration**: Deploy DB migrations to the production instance using `alembic upgrade head`.
- [ ] **Asset Validation**: Confirm that screenshots are correctly uploading to the Production Storage provider (S3 or Supabase Storage) rather than local disk.
- [ ] **CORS Lock-down**: Update `ALLOWED_ORIGINS` to include *only* the production frontend domain.

## 4. Operator Training & Feedback Loop 👥
- [ ] **Explainability Walkthrough**: Train the first shift of operators to use the "AI Automation Details" table to debug low-confidence fields.
- [ ] **Feedback Channel**: Establish a process for operators to flag "False Positives" which will be used to update the RAG `ResponsePool`.
- [ ] **Kill-switch Protocol**: Define the manual conditions under which the "AI Automation Kill-switch" should be toggled (e.g., unexpected merchant site layout changes).

## 5. Performance Baseline (Load Testing) ⚡
- [ ] **Concurrent Claiming**: Run 10 agents simultaneously and monitor `task_metrics` for any database locking issues.
- [ ] **Vector Search Latency**: Verify that RAG search remains `< 200ms` when the `ResponsePool` exceeds 1,000 entries.

## 6. v1.1 Board-Authorized Pilot Constraints (CRITICAL) 🛡️
- [ ] **Domain Whitelist Enforcement**: Confirm only tasks for `shareasale.com`, `impact.com`, and `cj.com` are permitted.
- [ ] **Mandatory Human-in-the-Loop**: Verify that "No Autonomous Submission" policy is active for every final submission.
- [ ] **Feedback Collection**: Ensure 1-5 operator confidence scores are mandatory before task completion.
- [ ] **Scope Freeze**: Acknowledge that further engineering expansion (adaptive agents, custom models) is frozen during the 30-day pilot.

## 7. Phase 7: Operational Tracking (Weekly) 📊
*   **Trust Distribution**: Success Rate vs. Operator Confidence (Target: Median ≥ 4.0).
*   **RoI Metric**: Cost per successful application (USD/Success).
*   **Intervention Rate**: Mean Time to Human Intervention (MTTHI).
*   **Failure Taxonomy**: Identify the Top 5 qualitative failure patterns for v1.2 prioritization.

---

### Final Assessment & Authorization
The system has received **Board-Level Authorization** to proceed with v1.1 Production Pilot. 

**Decision**: ✅ **PILOT GO**
**Authorization Status**: 
- **Tenant Limit**: 1 Pilot Tenant.
- **Human Gate**: Mandatory for all final submissions.
- **Engineering Status**: Fixed Scope / Stand-down.

"Automation is now accountability. Stand down on development; monitor for signal."
