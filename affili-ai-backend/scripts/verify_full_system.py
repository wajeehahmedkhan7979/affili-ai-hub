import pytest
import requests
import uuid
import time
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASS = "password"
TENANT_ID = "00000000-0000-0000-0000-000000000000"

def get_auth_token():
    print(f"Logging in as {ADMIN_EMAIL}...")
    resp = requests.post(f"{API_BASE}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS,
        "tenant_id": TENANT_ID
    })
    resp.raise_for_status()
    return resp.json()["access_token"]

def test_full_pipeline():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    # 1. Discover a program
    print("\n1. Triggering program discovery...")
    discover_resp = requests.post(f"{API_BASE}/tasks", headers=headers, json={
        "task_type": "DISCOVER_PROGRAM",
        "payload": {"url": "https://stripe.com"}
    })
    discover_resp.raise_for_status()
    task_id = discover_resp.json()["id"]
    print(f"✓ Discovery task created: {task_id}")
    
    # 2. Wait for completion (simulated via mock or agent)
    print("Waiting for task to be claimed...")
    time.sleep(2)
    
    # 3. Check health and metrics
    print("\n2. Checking system health...")
    health_resp = requests.get(f"{API_BASE}/health")
    print(f"✓ Health: {health_resp.json()['status']}")
    
    print("\n3. Checking SLA metrics...")
    sla_resp = requests.get(f"{API_BASE}/dashboards/sla", headers=headers)
    print(f"✓ Metric (MTTR): {sla_resp.json().get('mttr_minutes', 'N/A')} min")
    
    print("\n4. Checking AI Costs...")
    cost_resp = requests.get(f"{API_BASE}/governance/llm-costs", headers=headers)
    print(f"✓ Total Cost: ${cost_resp.json().get('total_cost_usd', '0.00')}")

    print("\n✓ End-to-End Baseline Test PASSED")

if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        exit(1)
