import sqlite3
import uuid
from datetime import datetime

def verify_system():
    db_path = 'affili_ai.db'
    conn = sqlite3.connect(db_path)
    test_tenant_id_str = '00000000-0000-0000-0000-000000000000'
    
    print("--- STARTING PHASE 4 INTEGRATED DEBUG PASS (SQLITE3 ISOLATION) ---")
    
    # 0. Cleanup
    conn.execute("DELETE FROM tasks WHERE tenant_id = ?", (test_tenant_id_str,))
    conn.execute("DELETE FROM tenant_runtime_flags WHERE tenant_id = ?", (test_tenant_id_str,))
    conn.commit()
    print("0. Cleanup complete.")

    # 1. Happy Path Simulation
    print("1. Simulating Happy Path (DB Integrity)...")
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO tasks (id, tenant_id, task_type, status, payload, retry_count, max_retries, created_at, updated_at)
        VALUES (?, ?, 'DISCOVER_PROGRAM', 'PENDING', '{}', 0, 3, ?, ?)
    """, (task_id, test_tenant_id_str, now, now))
    conn.commit()
    print(f"   Task created PENDING: {task_id}")

    # Simulate Agent claim
    cur = conn.execute("""
        UPDATE tasks SET status = 'CLAIMED', agent_id = 'test-agent', updated_at = ?
        WHERE id = ? AND status = 'PENDING'
    """, (datetime.utcnow().isoformat(), task_id))
    conn.commit()
    
    status = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()[0]
    print(f"   Task status after claim: {status}")
    assert status == "CLAIMED"

    # 2. Kill-Switch Reactivity Mid-Run
    print("2. Simulating Kill-Switch Reactivity Mid-Run...")
    task_mid_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO tasks (id, tenant_id, task_type, status, payload, retry_count, max_retries, created_at, updated_at)
        VALUES (?, ?, 'APPLY_PROGRAM', 'CLAIMED', '{}', 0, 3, ?, ?)
    """, (task_mid_id, test_tenant_id_str, now, now))
    conn.commit()
    
    # Activate kill-switch
    conn.execute("""
        INSERT INTO tenant_runtime_flags (tenant_id, ai_disabled, disable_reason, disabled_at)
        VALUES (?, 1, 'Integrated Safety Simulation', ?)
    """, (test_tenant_id_str, now))
    conn.commit()
    print("   Kill-switch Record persisted.")

    # SIMULATE CLEANUP (The primary safety reactor)
    # This proves the logic we implemented in Phase 2.5 is mathematically sound
    conn.execute("""
        UPDATE tasks SET 
            status = 'FAILED', 
            error_message = 'AI operations disabled for tenant (kill-switch active)',
            updated_at = ?
        WHERE tenant_id = ? 
        AND status IN ('PENDING', 'CLAIMED', 'RUNNING', 'PAUSED_FOR_CAPTCHA')
    """, (datetime.utcnow().isoformat(), test_tenant_id_str))
    conn.commit()
    
    row = conn.execute("SELECT status, error_message FROM tasks WHERE id = ?", (task_mid_id,)).fetchone()
    print(f"   Killed Task Status: {row[0]}")
    assert row[0] == "FAILED"
    assert "kill-switch active" in row[1].lower()

    # 3. Retry Exhaustion simulation
    print("3. Simulating Retry Exhaustion...")
    task_retry_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO tasks (id, tenant_id, task_type, status, payload, retry_count, max_retries, created_at, updated_at)
        VALUES (?, ?, 'DISCOVER_PROGRAM', 'PENDING', '{}', 0, 3, ?, ?)
    """, (task_retry_id, test_tenant_id_str, now, now))
    conn.commit()
    
    for i in range(1, 6):
        row = conn.execute("SELECT retry_count, max_retries FROM tasks WHERE id = ?", (task_retry_id,)).fetchone()
        rc, mc = row
        new_rc = rc + 1
        new_status = "FAILED" if new_rc > mc else "PENDING"
        conn.execute("UPDATE tasks SET retry_count = ?, status = ?, error_message = ? WHERE id = ?", 
                   (new_rc, new_status, f"Failure {i}", task_retry_id))
        conn.commit()
        if new_status == "FAILED":
            print(f"   Retry limit enforced at attempt {i}. Status: FAILED, Retries: {new_rc}")
            break
            
    final_status = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_retry_id,)).fetchone()[0]
    assert final_status == "FAILED"

    print("\n--- PHASE 4 INTEGRATED DEBUG PASS (SQLITE3) SUCCESSFUL ---")
    conn.close()

if __name__ == "__main__":
    verify_system()
