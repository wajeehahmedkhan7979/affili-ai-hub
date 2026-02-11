"""
Direct API Test - Minimal task creation for debugging
"""
import requests

API_BASE = "http://127.0.0.1:8000/api/v1"
TENANT_ID = "00000000-0000-0000-0000-000000000000"

# Login
print("1. Logging in...")
login_resp = requests.post(f"{API_BASE}/auth/login", json={
    "email": "admin@example.com",
    "password": "password",
    "tenant_id": TENANT_ID
})
print(f"   Status: {login_resp.status_code}")
if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    print(f"   Token: {token[:20]}...")
else:
    print(f"   Error: {login_resp.text}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant-ID": TENANT_ID
}

# Create minimal task
print("\n2. Creating task...")
task_payload = {
    "task_type": "DISCOVER_PROGRAM",
    "payload": {
        "url": "https://www.shareasale.com/info/",
        "program_domain": "shareasale.com"
    }
}

create_resp = requests.post(f"{API_BASE}/tasks", headers=headers, json=task_payload)
print(f"   Status: {create_resp.status_code}")
print(f"   Response: {create_resp.text[:200]}")

if create_resp.status_code == 201:
    task = create_resp.json()
    print(f"   ✓ Task created: {task['id']}")
else:
    print(f"   ✗ Failed to create task")

# List tasks
print("\n3. Listing tasks...")
list_resp = requests.get(f"{API_BASE}/tasks", headers=headers)
print(f"   Status: {list_resp.status_code}")
if list_resp.status_code == 200:
    tasks = list_resp.json()
    print(f"   Total tasks: {len(tasks)}")
