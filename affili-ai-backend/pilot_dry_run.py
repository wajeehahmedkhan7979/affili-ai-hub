import sqlite3
import uuid
import random
from datetime import datetime, timedelta

def pilot_dry_run():
    db_path = 'affili_ai.db'
    conn = sqlite3.connect(db_path)
    
    tenants = [
        '00000000-0000-0000-0000-000000000000', # Tenant A (Admin)
        '11111111-1111-1111-1111-111111111111', # Tenant B
        '22222222-2222-2222-2222-222222222222'  # Tenant C
    ]
    
    print("--- STARTING PHASE 6 PILOT DRY-RUN (50 TASKS) ---")
    
    # 0. Prep
    conn.execute("DELETE FROM tasks WHERE tenant_id IN (?, ?, ?)", tenants)
    conn.execute("DELETE FROM tenant_runtime_flags WHERE tenant_id IN (?, ?, ?)", tenants)
    conn.commit()
    print("0. Environment prepped.")

    # 1. Task Injection
    print("1. Injecting 50 tasks across 3 tenants...")
    task_ids = []
    for i in range(50):
        tid = random.choice(tenants)
        task_id = str(uuid.uuid4())
        task_ids.append((task_id, tid))
        now = datetime.utcnow().isoformat()
        conn.execute("""
            INSERT INTO tasks (id, tenant_id, task_type, status, payload, retry_count, max_retries, created_at, updated_at)
            VALUES (?, ?, ?, 'PENDING', '{}', 0, 3, ?, ?)
        """, (task_id, tid, random.choice(['DISCOVER_PROGRAM', 'APPLY_PROGRAM']), now, now))
    conn.commit()
    print(f"   Successfully injected 50 tasks.")

    # 2. Simulate Pilot Activity (Phased processing)
    print("2. Simulating Agent activity (Pickup and Completion)...")
    # 30 tasks complete successfully
    for i in range(30):
        task_id, tid = task_ids[i]
        now = datetime.utcnow().isoformat()
        conn.execute("""
            UPDATE tasks 
            SET status = 'COMPLETED', agent_id = 'agent-pilot-1', result = '{"success": true}', updated_at = ?, completed_at = ?
            WHERE id = ?
        """, (now, now, task_id))
    
    # 10 tasks fail and reach retry limit
    for i in range(30, 40):
        task_id, tid = task_ids[i]
        conn.execute("UPDATE tasks SET retry_count = 3, status = 'FAILED', error_message = 'Simulated pilot failure' WHERE id = ?", (task_id,))
    
    conn.commit()
    print("   Processed 40/50 tasks (30 Success, 10 Failed).")

    # 3. Governance Event (Kill-switch mid-run for Tenant B)
    print("3. Triggering Mid-Run Kill-switch for Tenant B...")
    target_tenant_b = tenants[1]
    now_ks = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO tenant_runtime_flags (tenant_id, ai_disabled, disable_reason, disabled_at)
        VALUES (?, 1, 'Pilot Dry-Run Emergency Simulation', ?)
    """, (target_tenant_b, now_ks))
    
    # Run the "Hammer of God" cleanup logic
    conn.execute("""
        UPDATE tasks SET 
            status = 'FAILED', 
            error_message = 'AI operations disabled for tenant (kill-switch active)',
            updated_at = ?
        WHERE tenant_id = ? 
        AND status IN ('PENDING', 'CLAIMED', 'RUNNING', 'PAUSED_FOR_CAPTCHA')
    """, (datetime.utcnow().isoformat(), target_tenant_b))
    conn.commit()
    print(f"   Kill-switch triggered for {target_tenant_b}. Cleanup executed.")

    # 4. Verification Check
    print("\n4. Final Integrity Check...")
    # Count task states
    results = conn.execute("SELECT status, count(*) FROM tasks GROUP BY status").fetchall()
    print("   Task Status Distribution:")
    for status, count in results:
        print(f"    - {status}: {count}")
    
    # Verify Tenant B has no active tasks
    active_b = conn.execute("SELECT count(*) FROM tasks WHERE tenant_id = ? AND status IN ('PENDING', 'CLAIMED', 'RUNNING')", (target_tenant_b,)).fetchone()[0]
    print(f"   Active tasks for Tenant B: {active_b} (Expected 0)")
    assert active_b == 0
    
    # Verify Kill-switch presence
    ks_count = conn.execute("SELECT count(*) FROM tenant_runtime_flags WHERE ai_disabled = 1").fetchone()[0]
    print(f"   Active Kill-switches: {ks_count} (Expected 1)")
    assert ks_count == 1

    print("\n--- PHASE 6 PILOT DRY-RUN SUCCESSFUL ---")
    conn.close()

if __name__ == "__main__":
    pilot_dry_run()
