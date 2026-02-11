"""
Quick script to list pilot tasks and their current status
"""
import requests
import os
from datetime import datetime

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TENANT_ID = "00000000-0000-0000-0000-000000000000"

def get_auth_token():
    resp = requests.post(f"{API_BASE}/auth/login", json={
        "email": "admin@example.com",
        "password": "password",
        "tenant_id": TENANT_ID
    })
    resp.raise_for_status()
    return resp.json()["access_token"]

def list_tasks():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    resp = requests.get(f"{API_BASE}/tasks", headers=headers)
    resp.raise_for_status()
    tasks = resp.json()
    
    print(f"\n--- PILOT TASKS STATUS ---")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Tasks: {len(tasks)}\n")
    
    # Filter for pilot test tasks
    pilot_tasks = [t for t in tasks if t.get('payload', {}).get('test_mode') == True]
    
    if pilot_tasks:
        print(f"Pilot Test Tasks: {len(pilot_tasks)}")
        for i, task in enumerate(pilot_tasks, 1):
            payload = task.get('payload', {})
            print(f"\n{i}. Task ID: {task['id']}")
            print(f"   Type: {task['task_type']}")
            print(f"   Domain: {payload.get('program_domain', 'unknown')}")
            print(f"   Status: {task['status']}")
            print(f"   Created: {task['created_at']}")
            if task.get('agent_id'):
                print(f"   Agent: {task['agent_id']}")
    else:
        print("No pilot test tasks found.")
    
    # Show non-test tasks count
    other_tasks = [t for t in tasks if not t.get('payload', {}).get('test_mode')]
    if other_tasks:
        print(f"\n\nOther Tasks: {len(other_tasks)} (not part of pilot test)")

if __name__ == "__main__":
    list_tasks()
