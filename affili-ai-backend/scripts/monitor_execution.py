"""
Detailed Pilot Task Execution Monitor
Shows full status, progress, and agent behavior for Step 3 observation
"""
import requests
import os
import json
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

def monitor_execution():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    resp = requests.get(f"{API_BASE}/tasks", headers=headers)
    resp.raise_for_status()
    tasks = resp.json()
    
    print(f"\n=== PILOT EXECUTION MONITOR (Step 3) ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Filter pilot tasks
    pilot_tasks = [t for t in tasks if t.get('payload', {}).get('test_mode') == True]
    
    if not pilot_tasks:
        print("No pilot tasks found.")
        return
    
    # Status summary
    status_counts = {}
    for task in pilot_tasks:
        status = task['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("STATUS SUMMARY:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print(f"\n--- TASK DETAILS ---\n")
    
    for i, task in enumerate(pilot_tasks, 1):
        payload = task.get('payload', {})
        domain = payload.get('program_domain', 'unknown')
        
        print(f"{i}. {domain.upper()}")
        print(f"   ID: {task['id']}")
        print(f"   Status: {task['status']}")
        print(f"   Type: {task['task_type']}")
        
        if task.get('agent_id'):
            print(f"   Agent: {task['agent_id']}")
        
        if task.get('retry_count', 0) > 0:
            print(f"   Retries: {task['retry_count']}/{task.get('max_retries', 3)}")
        
        # Timestamps
        print(f"   Created: {task.get('created_at', 'N/A')}")
        if task.get('claimed_at'):
            print(f"   Claimed: {task['claimed_at']}")
        if task.get('started_at'):
            print(f"   Started: {task['started_at']}")
        if task.get('completed_at'):
            print(f"   Completed: {task['completed_at']}")
        
        # Results/Error
        if task.get('result'):
            result = task['result']
            if isinstance(result, dict):
                print(f"   Result Keys: {list(result.keys())}")
            else:
                print(f"   Result: {str(result)[:100]}")
        
        if task.get('error_message'):
            print(f"   Error: {task['error_message'][:100]}")
        
        # Operator confidence (Step 4 data)
        if task.get('operator_confidence'):
            print(f"   Operator Confidence: {task['operator_confidence']}/5")
        
        print()
    
    print(f"\n--- OBSERVATION NOTES ---")
    print(f"Total Pilot Tasks: {len(pilot_tasks)}")
    print(f"Agents Active: {len(set(t.get('agent_id') for t in pilot_tasks if t.get('agent_id')))}")
    
    # Check for policy violations or anomalies
    high_retry = [t for t in pilot_tasks if t.get('retry_count', 0) > 2]
    if high_retry:
        print(f"⚠ HIGH RETRY COUNT: {len(high_retry)} task(s) approaching retry ceiling")
    
    completed = [t for t in pilot_tasks if t['status'] in ['COMPLETED', 'FAILED']]
    if completed:
        print(f"\n✓ {len(completed)} task(s) ready for Human-in-the-Loop review (Step 4)")

if __name__ == "__main__":
    monitor_execution()
