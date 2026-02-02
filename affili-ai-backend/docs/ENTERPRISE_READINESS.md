# Enterprise Technical Readiness — AFFILI-AI HUB

## 1. System Architecture
AFFILI-AI HUB is built as a distributed, multi-tenant automation platform.
*   **Backend:** FastAPI (Python) - High-performance asynchronous API.
*   **Database:** PostgreSQL (Supabase) - Utilizing `JSONB` for flexible program schemas and `FOR UPDATE SKIP LOCKED` for atomic task distribution.
*   **Agent Layer:** Playwright-based containerized agents polling a centralized task queue.

## 2. Scaling Model
The platform is designed for horizontal scalability:
*   **API Scaling:** Stateless API nodes can be scaled behind a Load Balancer/Ingress (HPA configured for CPU/Memory).
*   **Agent Scaling:** Agents are grouped into pools (Discovery vs. Application). Scaling is independent based on queue depth.
*   **Tenant Scaling:** Multi-tenancy is enforced at the data layer, allowing thousands of isolated tenants on a single shared cluster.

## 3. Reliability & Recovery
*   **Heartbeat Mechanism:** Agents send heartbeats every 30s. If an agent crashes, the backend detects the timeout and reverts the task to `PENDING` for re-claiming.
*   **Atomic Claiming:** Prevents double-execution of expensive automation tasks.
*   **Evidence Capture:** Every task execution captures logs and screenshots (Before/After/Error), providing a full audit trail for compliance and debugging.

## 4. Compliance & Policy
*   **Audit Logging:** All administrative actions and task state changes are logged with user and tenant context.
*   **Legal Hold:** Support for data retention policies and legal hold on application evidence.
*   **RBAC:** Granular access control ensures sensitive operations are restricted to authorized personnel.

## 5. Technology Choices
*   **Why PostgreSQL + SKIP LOCKED?** Avoids the complexity and overhead of Redis/Kafka for task queueing while maintaining strict ACID guarantees and high concurrency.
*   **Why Playwright?** Industry-standard for browser automation, providing superior reliability and evidence capture compared to Selenium or Puppeteer.
*   **CAPTCHA Strategy:** Intentionally excluded to focus on high-integrity, white-hat affiliate discovery and management.
