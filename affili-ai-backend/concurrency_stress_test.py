import threading
import uuid
import time
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.db.session import SessionLocal
from app.services.task_dispatcher import create_task, find_and_claim_task
from app.models.task import Task, TaskStatus
from app.services.cost_governance import cost_governance

# Configuration
NUM_WORKERS = 10
NUM_TASKS = 50
TENANT_ID = "66f36618-29a3-4a1e-8e8e-67016258410e" # Static test tenant from diagnostic

from app.core.tenant import set_tenant_id

def virtual_worker(worker_id):
    """Simulates a worker trying to claim as many tasks as possible."""
    claimed_count = 0
    errors = []
    
    # Wait for the starting gun
    time.sleep(0.5) 
    
    # Attempt to claim tasks until none are left
    while True:
        db = SessionLocal()
        try:
            # Set context for tenant_id (needed by dispatcher)
            set_tenant_id(TENANT_ID)
            
            task = find_and_claim_task(db, agent_id=f"stress-worker-{worker_id}")
            if not task:
                break # No more tasks
            
            claimed_count += 1
            # Simulate some work
            # time.sleep(0.01)
            
        except Exception:
            errors.append(traceback.format_exc())
        finally:
            db.close()
            
    return claimed_count, errors

def run_concurrency_test():
    print(f"--- PHASE 9 CONCURRENCY STRESS TEST (Workers: {NUM_WORKERS}, Tasks: {NUM_TASKS}) ---")
    
    from app.db.base import Base
    from app.db.session import get_engine_instance
    engine = get_engine_instance()
    Base.metadata.create_all(engine)
    
    db = SessionLocal()
    import os
    os.environ["TENANT_ID"] = TENANT_ID
    
    # 1. Clear existing tasks for clean run
    db.query(Task).filter(Task.tenant_id == uuid.UUID(TENANT_ID)).delete()
    db.commit()
    
    # 2. Deactivate Kill-Switch for test start
    cost_governance.disable_tenant_killswitch(db, uuid.UUID(TENANT_ID))
    
    # 3. Seed tasks
    print(f"Seeding {NUM_TASKS} tasks...")
    for i in range(NUM_TASKS):
        create_task(db, task_type="STRESS_TEST", payload={"index": i})
    db.commit()
    
    # SYSTEM_USER_ID for kill-switch activation if needed
    SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

    # 4. Launch parallel workers
    print("Launching workers...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(virtual_worker, i): i for i in range(NUM_WORKERS)}
        
        # Kill-switch interjection simulation
        # At 0.2 seconds into the race, enable kill-switch
        # time.sleep(0.1)
        # print("\n[EMERGENCY] Activating KILL-SWITCH mid-run...")
        # cost_governance.enable_tenant_killswitch(db, uuid.UUID(TENANT_ID), reason="Stress Test Halt", disabled_by=SYSTEM_USER_ID)
        
        results = []
        for future in as_completed(futures):
            results.append(future.result())
            
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.2f}s")
    
    # 5. Analysis
    total_claimed = sum(r[0] for r in results)
    all_errors = [e for r in results for e in r[1]]
    
    print("\n--- RESULTS ---")
    print(f"Total Tasks Created: {NUM_TASKS}")
    print(f"Total Tasks Claimed: {total_claimed}")
    
    # Verify that every task was claimed exactly once
    db = SessionLocal()
    claimed_tasks = db.query(Task).filter(
        Task.tenant_id == uuid.UUID(TENANT_ID),
        Task.status == TaskStatus.CLAIMED
    ).all()
    unique_claimed = len(set(t.id for t in claimed_tasks))
    
    print(f"Unique Tasks in DB: {unique_claimed}")
    
    if total_claimed == NUM_TASKS and unique_claimed == NUM_TASKS:
        print("PASS: Atomicity verified. Zero double-claims.")
    else:
        print("FAIL: Task count mismatch. Possible race condition!")
        
    if all_errors:
        print(f"Errors encountered: {len(all_errors)}")
        for err in all_errors[:5]:
            print(f"  - {err}")
            
    return total_claimed == NUM_TASKS and unique_claimed == NUM_TASKS

if __name__ == "__main__":
    success = run_concurrency_test()
    import sys
    sys.exit(0 if success else 1)
