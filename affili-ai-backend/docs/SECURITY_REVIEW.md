# Security Review & Threat Model — AFFILI-AI HUB

## 1. Overview
This document outlines the security posture, identified threats, and mitigation strategies for the AFFILI-AI HUB platform.

## 2. Threat Model

### T1: API Abuse & Unauthorized Access
*   **Risk:** Attackers attempting to access tenant data or trigger unauthorized automation.
*   **Mitigation:**
    *   RBAC (Owner, Admin, Operator, Viewer) implemented at the API level.
    *   JWT-based authentication with ES256 signatures.
    *   Strict tenant isolation using `tenant_id` on all database queries (Row-Level Security concept).
    *   Rate limiting on all public-facing endpoints.

### T2: Tenant Escape (Cross-Tenant Data Leakage)
*   **Risk:** One tenant accessing another tenant's programs, applications, or credentials.
*   **Mitigation:**
    *   Atomic database operations ensuring `tenant_id` parity.
    *   Validation in service layer to prevent cross-tenant ID referencing.
    *   Future: PostgreSQL Row Level Security (RLS) implementation on Supabase.

### T3: Agent Compromise & Browser Risks
*   **Risk:** Malware in a target website exploiting Playwright's browser instance.
*   **Mitigation:**
    *   Agents run in isolated Docker containers with restricted network access.
    *   Headless mode enabled by default.
    *   No persistent browser profiles; fresh context for every task.
    *   Screenshots and logs stored in isolated volumes, not accessible to the browser process.

### T4: Credential Exposure
*   **Risk:** Affiliate program credentials leaked from the database.
*   **Mitigation:**
    *   Encrypted storage for sensitive fields in the `credentials` table.
    *   Environment variables for system-level secrets (Supabase keys).
    *   Kubernetes Secrets management for production deployments.

## 3. Supply Chain Risks
*   **Risk:** Compromised dependencies in `requirements.txt`.
*   **Mitigation:**
    *   Pinned versions for all core dependencies.
    *   Use of official, scanned base images (Python Slim, Microsoft Playwright).

## 4. Residual Risks
*   **CAPTCHA Solving:** Intentionally excluded. High-risk/bot-like behavior is avoided by design.
*   **IP Reputation:** Agents sharing egress IPs might get flagged. Recommended mitigation: Use of rotating proxy services.

## 5. Out of Scope
*   Physical security of Supabase/Cloud provider data centers.
*   Client-side security of the user's browser (beyond CORS).
