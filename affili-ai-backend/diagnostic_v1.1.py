import sys
import sqlite3
from datetime import datetime, timedelta

def run_diagnostics():
    db_path = 'affili_ai.db'
    print("--- AFFILI-AI HUB v1.1 PILOT DIAGNOSTIC TOOL (ISOLATED) ---")
    
    issues = []
    
    try:
        conn = sqlite3.connect(db_path)
        print("\n[1] Checking Database Connectivity...")
        conn.execute("SELECT 1")
        print("    SUCCESS: Connected to sqlite3 database.")
    except Exception as e:
        print(f"    FAILURE: Could not connect to database: {e}")
        return False

    # 2. Table Integrity
    print("\n[2] Verifying Core Tables (v1.1 Baseline)...")
    critical_tables = [
        'tenants', 'users', 'tasks', 'programs', 
        'tenant_runtime_flags', 'operator_action_logs', 
        'task_metrics', 'llm_usage_logs'
    ]
    
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [r[0] for r in cur.fetchall()]
        
        for table in critical_tables:
            if table in existing_tables:
                print(f"    [OK] {table}")
            else:
                print(f"    [MISSING] {table}")
                issues.append(f"Missing critical table: {table}")
    except Exception as e:
        print(f"    Error during table check: {e}")
        issues.append(f"Table check error: {e}")

    # 3. Task Hygiene
    print("\n[3] Checking Task Queue Hygiene...")
    try:
        # Total tasks
        total = conn.execute("SELECT count(*) FROM tasks").fetchone()[0]
        # Active tasks
        active = conn.execute("SELECT count(*) FROM tasks WHERE status IN ('PENDING', 'CLAIMED', 'RUNNING', 'PAUSED_FOR_CAPTCHA')").fetchone()[0]
        # Stale tasks (> 1 hour)
        limit = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        stale = conn.execute("SELECT count(*) FROM tasks WHERE status = 'CLAIMED' AND updated_at < ?", (limit,)).fetchone()[0]
        
        print(f"    Total Tasks: {total}")
        print(f"    Active Tasks: {active}")
        if stale > 0:
            print(f"    [WARNING] Found {stale} stale CLAIMED tasks.")
            issues.append(f"Found {stale} stale tasks")
        else:
            print("    [OK] No stale tasks detected.")
    except Exception as e:
        print(f"    Error during hygiene check: {e}")

    # 4. Governance Status
    print("\n[4] Pilot Governance Status...")
    try:
        cur = conn.execute("SELECT tenant_id, disable_reason, disabled_at FROM tenant_runtime_flags WHERE ai_disabled = 1")
        switches = cur.fetchall()
        if switches:
            for tid, reason, dat in switches:
                print(f"    [DISABLED] Tenant: {tid} | Reason: {reason}")
        else:
            print("    [OK] AI Operations globally ENABLED (No active kill-switches).")
    except Exception as e:
        print(f"    Error during governance check: {e}")

    # Final Report
    print("\n" + "="*50)
    if not issues:
        print("PILOT READINESS: [GO] - System verified for v1.1.")
    else:
        print(f"PILOT READINESS: [NO-GO] - {len(issues)} Issues Detected.")
        for issue in issues:
            print(f"  - {issue}")
    print("="*50)
    
    conn.close()
    return len(issues) == 0

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
