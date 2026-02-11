"""
Pilot Task Injection Script - Day 1 Operations Test

Creates 2-3 controlled test tasks for whitelisted domains only.
Aligned with PILOT_OPERATIONS_STRATEGY.md (Step 2).
"""
import requests
import os
from datetime import datetime

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASS = "password"
TENANT_ID = "00000000-0000-0000-0000-000000000000"

# Board-approved whitelist
WHITELISTED_DOMAINS = ["shareasale.com", "impact.com", "cj.com"]

def get_auth_token():
    print(f"Authenticating as {ADMIN_EMAIL}...")
    resp = requests.post(f"{API_BASE}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS,
        "tenant_id": TENANT_ID
    })
    resp.raise_for_status()
    return resp.json()["access_token"]

def inject_pilot_tasks():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    print("\n--- PILOT TASK INJECTION (Step 2) ---")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Whitelisted Domains: {', '.join(WHITELISTED_DOMAINS)}\n")
    
    # Test task payloads (2-3 tasks for Day 1)
    test_tasks = [
        {
            "task_type": "DISCOVER_PROGRAM",
            "payload": {
                "url": "https://www.shareasale.com/info/",
                "program_domain": "shareasale.com",
                "test_mode": True,
                "pilot_day": 1
            }
        },
        {
            "task_type": "DISCOVER_PROGRAM",
            "payload": {
                "url": "https://impact.com/partnership-cloud/",
                "program_domain": "impact.com",
                "test_mode": True,
                "pilot_day": 1
            }
        },
        {
            "task_type": "DISCOVER_PROGRAM",
            "payload": {
                "url": "https://www.cj.com/advertiser",
                "program_domain": "cj.com",
                "test_mode": True,
                "pilot_day": 1
            }
        }
    ]
    
    created_tasks = []
    for i, task_payload in enumerate(test_tasks, 1):
        print(f"Task {i}: Creating {task_payload['task_type']} for {task_payload['payload']['program_domain']}...")
        
        try:
            resp = requests.post(f"{API_BASE}/tasks", headers=headers, json=task_payload)
            resp.raise_for_status()
            task = resp.json()
            created_tasks.append(task)
            print(f"  ✓ Created: {task['id']}")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  ✗ BLOCKED by policy (expected for safety verification)")
            elif e.response.status_code == 429:
                print(f"  ✗ THROTTLED (program limit reached)")
            else:
                print(f"  ✗ Failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n--- INJECTION COMPLETE ---")
    print(f"Tasks Created: {len(created_tasks)}")
    print(f"Next Step: Operator Observation (Step 3)")
    print(f"Required Action: Human review and confidence rating (1-5 stars)\n")
    
    return created_tasks

if __name__ == "__main__":
    try:
        inject_pilot_tasks()
    except Exception as e:
        print(f"❌ Task injection failed: {e}")
        exit(1)
