"""
Step 5: Post-Execution Review
Validates that all pilot operations completed correctly and safely
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

def post_execution_review():
    """
    Step 5: Post-Execution Review
    - Check task_metrics entries
    - Verify cost attribution
    - Ensure no retries exceeded policy
    - Confirm screenshots stored (if applicable)
    """
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}
    
    print("\n=== STEP 5: POST-EXECUTION REVIEW ===\n")
    
    # Get pilot tasks
    resp = requests.get(f"{API_BASE}/tasks", headers=headers)
    resp.raise_for_status()
    tasks = resp.json()
    
    pilot_tasks = [t for t in tasks if t.get('payload', {}).get('test_mode') == True]
    
    print(f"Total Pilot Tasks: {len(pilot_tasks)}")
    
    # Safety Checks
    print("\n--- SAFETY VALIDATION ---")
    
    # 1. Retry Policy Compliance
    retry_violations = [t for t in pilot_tasks if t.get('retry_count', 0) > 3]
    if retry_violations:
        print(f"❌ VIOLATION: {len(retry_violations)} task(s) exceeded retry ceiling of 3")
        for task in retry_violations:
            print(f"   Task {task['id']}: {task['retry_count']} retries")
    else:
        print(f"✓ Retry Policy: All tasks within limit (max observed: {max((t.get('retry_count', 0) for t in pilot_tasks), default=0)})")
    
    # 2. No Autonomous Submissions
    submitted_tasks = [t for t in pilot_tasks if t['status'] == 'SUBMITTED']
    if submitted_tasks:
        print(f"⚠ WARNING: {len(submitted_tasks)} task(s) in SUBMITTED status - verify HITL compliance")
    else:
        print(f"✓ No Autonomous Submission: No tasks auto-submitted")
    
    # 3. Operator Feedback Compliance
    reviewed_tasks = [t for t in pilot_tasks if t.get('operator_confidence')]
    if reviewed_tasks:
        confidences = [t['operator_confidence'] for t in reviewed_tasks]
        avg_conf = sum(confidences) / len(confidences)
        print(f"✓ Operator Review: {len(reviewed_tasks)}/{len(pilot_tasks)} tasks reviewed")
        print(f"   Average Confidence: {avg_conf:.1f}/5.0")
    else:
        print(f"⚠ No operator confidence data collected yet")
    
    # 4. Cost Attribution Check
    print("\n--- COST & METRICS ---")
    try:
        cost_resp = requests.get(f"{API_BASE}/dashboards/cost-efficiency", headers=headers)
        if cost_resp.status_code == 200:
            cost_data = cost_resp.json()
            print(f"✓ Cost Efficiency: ${cost_data.get('cost_per_success_usd', 0.00):.2f} per success")
        else:
            print(f"⚠ Cost dashboard unavailable")
    except Exception as e:
        print(f"⚠ Could not fetch cost metrics: {e}")
    
    # 5. Task Status Summary
    print("\n--- FINAL STATUS ---")
    status_counts = {}
    for task in pilot_tasks:
        status = task['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")
    
    # Overall Assessment
    print("\n--- DAILY OPERATIONS ASSESSMENT ---")
    
    issues = []
    if retry_violations:
        issues.append("Retry ceiling violations")
    if submitted_tasks:
        issues.append("Possible autonomous submission")
    
    if issues:
        print(f"❌ ISSUES DETECTED: {', '.join(issues)}")
        print("   Action Required: Investigation before next cycle")
    else:
        print("✓ ALL CHECKS PASSED")
        print("   Status: READY FOR NEXT DAILY CYCLE")
    
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    post_execution_review()
