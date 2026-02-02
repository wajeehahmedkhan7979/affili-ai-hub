"""
Smoke script (NOT a pytest test).

Creates a Stripe Connect Program + Application via API and observes the
corresponding APPLY_PROGRAM task until it completes.

Prereqs:
- Backend running at API_BASE_URL (default http://127.0.0.1:8000)
- Agent running (python agent/main.py)
- Playwright browsers installed (playwright install chromium)
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _print_title(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _post_json(client: httpx.Client, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = client.post(f"{API_BASE_URL}{path}", json=payload, timeout=20.0)
    r.raise_for_status()
    return r.json()


def _get_json(client: httpx.Client, path: str) -> Any:
    r = client.get(f"{API_BASE_URL}{path}", timeout=20.0)
    r.raise_for_status()
    return r.json()


def main() -> int:
    _print_title("AFFILI-AI Smoke: APPLY Stripe Connect")
    print(f"API_BASE_URL: {API_BASE_URL}")

    with httpx.Client() as client:
        _print_title("1) Create Program (Stripe Connect)")
        program = _post_json(
            client,
            "/api/v1/programs",
            {
                "name": "Stripe Connect",
                "description": "Stripe Connect partner signup (smoke)",
                "affiliate_url": "https://stripe.com/connect/partners",
                "commission_rate": 0.0,
                "terms": "N/A",
                "is_active": True,
            },
        )
        program_id = program["id"]
        print(f"Created program_id={program_id}")

        _print_title("2) Create Application (should enqueue APPLY_PROGRAM task)")
        application = _post_json(
            client,
            "/api/v1/applications",
            {
                "program_id": program_id,
                "user_email": "smoke@example.com",
                "name": "Smoke Test User",
                "website": "https://example.com",
            },
        )
        application_id = application["id"]
        print(f"Created application_id={application_id}")

        _print_title("3) Find the created APPLY_PROGRAM task")
        # Fetch recent tasks and locate the one for this application_id
        tasks = _get_json(client, "/api/v1/tasks?limit=100")
        task: Optional[Dict[str, Any]] = None
        for t in tasks:
            payload = t.get("payload") or {}
            if (
                t.get("task_type") == "APPLY_PROGRAM"
                and payload.get("application_id") == application_id
            ):
                task = t
                break

        if not task:
            print("ERROR: Could not find APPLY_PROGRAM task for this application_id.")
            print("Tasks returned (first 5):")
            for t in tasks[:5]:
                print(f"- id={t.get('id')} type={t.get('task_type')} status={t.get('status')} payload={t.get('payload')}")
            return 1

        task_id = task["id"]
        print(f"Found task_id={task_id} status={task.get('status')}")
        print("Task payload:")
        print(task.get("payload"))

        _print_title("4) Wait for agent to claim + complete task")
        # Agent should claim and run it; we just poll.
        deadline = time.time() + 180  # 3 minutes
        last_status = None
        while time.time() < deadline:
            t = _get_json(client, f"/api/v1/tasks/{task_id}")
            status = t.get("status")
            if status != last_status:
                print(f"- status -> {status} (agent_id={t.get('agent_id')})")
                last_status = status

            if status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)

        final = _get_json(client, f"/api/v1/tasks/{task_id}")
        print("\nFinal task status:", final.get("status"))
        if final.get("error_message"):
            print("Error:", final.get("error_message"))

        screenshots = (final.get("result") or {}).get("screenshots") or {}
        after_path = screenshots.get("after") or final.get("screenshot_url")
        print("Screenshot (after):", after_path)

        # Local evidence check (relative to backend working dir)
        local_dir = os.path.join("storage", "screenshots", str(task_id))
        print("Expected screenshot dir:", local_dir)
        if os.path.isdir(local_dir):
            files = os.listdir(local_dir)
            print(f"Screenshot files ({len(files)}):")
            for f in files:
                print(f"- {f}")
        else:
            print("INFO: Screenshot directory not found locally yet.")
            print("      This is expected until the agent claims and runs the task.")
            print("      Ensure the agent is running from the backend directory so relative paths match.")

        if final.get("status") == "COMPLETED":
            print("\nSMOKE PASS: task completed and evidence captured (check files above).")
            return 0
        else:
            print("\nSMOKE INCOMPLETE/FAIL: task did not complete successfully (is the agent running?).")
            return 2


if __name__ == "__main__":
    raise SystemExit(main())

