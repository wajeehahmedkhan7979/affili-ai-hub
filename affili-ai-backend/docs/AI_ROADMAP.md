# AI & Automation Roadmap — AFFILI-AI HUB

## 1. Automation Philosophy
Automations are deterministic. AI is advisory. The goal is 100% accuracy in affiliate program discovery and application, not 100% autonomy.

## 2. Core Components

### Playwright Automation (Implemented)
*   **Role:** The "Hands" of the platform.
*   **Usage:** Navigating websites, filling forms, clicking buttons, capturing evidence.
*   **Dependencies:** No AI dependency for core execution.

### LLM Usage (The "Brain")
*   **Role:** Intelligent guidance and error recovery.
*   **Integration Points:**
    *   **Form Understanding:** Parsing complex HTML forms to map fields (e.g., "Company Name" vs. "Brand Name").
    *   **Selector Recovery:** If a hardcoded selector fails, use LLM to find the new target based on UI context.
    *   **Error Interpretation:** Reading logs/screenshots to classify failures more accurately than regex.

### RAG (Retrieval Augmented Generation)
*   **Role:** The "Memory" and "Policy Expert".
*   **Integration Points:**
    *   **Program Analysis:** Indexing program terms of service to answer: "Is PPC allowed for this program?"
    *   **Agent Guidance:** Providing context to the LLM brain based on historical successes/failures for similar sites.

## 3. Implementation Sequence

### Level 1: Stable Automation (Current)
*   Hardcoded scripts + robust failure classification.
*   Manual selector mapping.

### Level 2: DOM-Aware Guidance (Next)
*   Capture DOM snapshots during execution.
*   Use LLM to generate/verify selectors dynamically if execution fails.

### Level 3: RAG-Enhanced Discovery
*   Index affiliate program documentation.
*   Automated checking of program compliance before application.

### Level 4: Self-Healing Agents
*   Agents use previous success patterns to navigate entirely new affiliate platforms with minimal human intervention.

## 4. Human-In-The-Loop (HITL)
*   **Monitoring:** Humans review screenshots of failed tasks.
*   **Intervention:** Humans solve CAPTCHAs or map unknown fields, which feeds back into the RAG memory for future tasks.
