# 📋 AFFILI-AI HUB: v1.1 Operations Test & Observation Strategy

**Status:** ✅ Operations Mode ACTIVE  
**Baseline:** v1.1 (Immutable)  
**Engineering Status:** 🔒 FROZEN (Incident Response Only)

---

## 1. Operating Principle
The goal of the pilot is not performance maximization. We are answering four board-level questions:
- Is the system safe under real usage?
- Does trust increase or decay over time?
- Are humans meaningfully in control?
- Is cost proportional to value delivered?

---

## 2. Test Categories
| ✅ Allowed Actions | ❌ PROHIBITED Actions |
| :--- | :--- |
| Normal task creation & execution | New domains / Program additions |
| Operator review, pause, resume, cancel | New automation / RAG logic |
| HITL verification flows | Removing HITL gates |
| Observability & reporting | Bypassing confidence thresholds |
| Controlled concurrency (within caps) | Load tests beyond approved limits |

---

## 3. Daily Operations Test Loop
*Mandatory once per day, per pilot tenant.*

### Step 1: System Health Gate
- **API Health**: `200 OK`
- **DB Connectivity**: `Accepting Connections`
- **Agent Heartbeat**: `Active`
- **Cost Kill-switch**: `OFF`
- *If any fail: **STOP**. Do not proceed.*

### Step 2: Controlled Task Injection
- Create **2–5 tasks only**.
- Domain must be on whitelist (`shareasale.com`, `impact.com`, `cj.com`).

### Step 3: Execution Observation
Observe field confidence, RAG sources, and retry behavior. **Do not intervene unless required by policy.**

### Step 4: Human-in-the-Loop Gate
- Review every filled form.
- Confirm/Reject AI decisions.
- **Record Operator Confidence (1–5)**. Reasoning required for scores ≤ 3.

---

## 4. Weekly Deep Validation
### A. Trust Distribution Review
- Monitor Median Operator Confidence (Target: ≥ 4.0).
- Watch for downward drift variance.

### B. Cost-per-Success Analysis
- Compute: `Total LLM Cost / Successful Tasks`.
- Evaluate stability and retry inflation.

### C. Failure Mode Taxonomy
Classify failures into: UI Variance, Merchant Logic, RAG Mismatch, Human Rejection, or Safety Gate Rejection.

---

## 5. 🚨 Safety Incident Playbook
**Immediate Kill-switch triggers:**
- Submission attempted without HITL.
- Domain outside whitelist touched.
- Confidence gating bypassed.
- Retry count > 3 observed.
- Cost spike > 2× baseline.

**Protocol:** 1. Trigger Kill-switch -> 2. Cancel Tasks -> 3. Preserve Logs -> 4. Notify Engineering Engineering.

---

## 6. Success Criteria for v1.2
- ≥ 200 pilot tasks completed.
- Stable trust distribution (Median ≥ 4.0).
- **ZERO** safety incidents.
- Cost-per-success within expected envelope.

---

## 7. Operational Deliverables (Day 30)
1. Trust distribution chart.
2. Cost-per-success trend.
3. Top 5 failure modes taxonomy.
4. Recommendation: (Proceed / Extend Observation / Redesign).

---

**"Automation is now accountability. Stand down on development; monitor for signal."**
