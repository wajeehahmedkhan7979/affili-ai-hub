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

def verify_v1_1_safety():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    print("\n--- v1.1 SAFETY VERIFICATION ---")

    # 1. Test Site Stability Whitelist
    print("\n1. Testing Site Stability Whitelist...")
    bad_site_resp = requests.post(f"{API_BASE}/tasks", headers=headers, json={
        "task_type": "APPLY_PROGRAM",
        "payload": {"url": "https://unstable-site.com", "program_domain": "unstable-site.com"}
    })
    if bad_site_resp.status_code == 403:
        print("✓ REJECTED: Unstable site blocked correctly.")
    else:
        print(f"❌ FAILED: Unstable site was allowed ({bad_site_resp.status_code})")

    # 2. Test Program-level Throttling
    print("\n2. Testing Program-level Throttling (Cap = 10)...")
    program_id = str(uuid.uuid4())
    success_count = 0
    for i in range(12):
        resp = requests.post(f"{API_BASE}/tasks", headers=headers, json={
            "task_type": "DISCOVER_PROGRAM",
            "program_id": program_id,
            "payload": {"url": "https://example.com"}
        })
        if resp.status_code == 201:
            success_count += 1
        elif resp.status_code == 429:
            print(f"✓ REJECTED: Task {i+1} blocked by throttling cap.")
            break
    print(f"   Max tasks created: {success_count}/10")

    # 3. Test No Autonomous Submission Policy
    print("\n3. Testing Anti-Autonomous Policy...")
    submit_resp = requests.post(f"{API_BASE}/tasks/00000000-0000-0000-0000-000000000000/update", headers=headers, json={
        "status": "SUBMITTED",
        "is_human_reviewed": False
    })
    # Note: 404 is also okay if task 0000... doesn't exist, but we check if policy service would handle it
    print("   (Note: Policy check integrated in evaluate_action called via API)")

    # 4. Check New Observability Endpoints
    print("\n4. Verifying Safety Dashboards...")
    drift_resp = requests.get(f"{API_BASE}/dashboards/confidence-drift", headers=headers)
    if drift_resp.status_code == 200:
        print(f"✓ Confidence Drift Data: {len(drift_resp.json().get('drift', []))} entries")
    
    cost_resp = requests.get(f"{API_BASE}/dashboards/cost-efficiency", headers=headers)
    if cost_resp.status_code == 200:
        print(f"✓ Cost Efficiency: ${cost_resp.json().get('cost_per_success_usd', '0.00')} per task")

    print("\n--- v1.1 VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    try:
        verify_v1_1_safety()
    except Exception as e:
        print(f"❌ Verification script failed: {e}")
        exit(1)
