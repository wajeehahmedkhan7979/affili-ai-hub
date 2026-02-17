"""
Verification script for Phase 21.3: Parallel Execution.
Tests Fan-Out and Fan-In logic.
"""

from sqlalchemy.orm import Session
from app.db.session import get_engine_instance
from app.db.base import Base
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStatus, WorkflowStepInstance
from app.models.task import Task, TaskStatus
from app.models.tenant import Tenant
from app.services.workflow_service import workflow_service
from app.services.task_dispatcher import update_task_status
from app.core.tenant import set_tenant_id
import uuid
import time
import json

# Setup Database
engine = get_engine_instance()
Base.metadata.create_all(bind=engine)

def verify_parallel():
    print("\n=== TEST 3: Parallel Execution (Fan-Out / Fan-In) ===")
    with Session(engine) as db:
        tenant = db.query(Tenant).first()
        if not tenant:
            print("ERROR: No tenant found")
            return
        
        tenant_id = str(tenant.id)
        set_tenant_id(tenant_id)
        
        # Define Workflow with Parallel Step
        # Start -> Parallel(Task A, Task B) -> End
        definition = {
            "steps": [
                {
                    "id": "step_start",
                    "type": "DISCOVER_PROGRAM",
                    "payload": {"query": "start"},
                    "next": "step_parallel"
                },
                {
                    "id": "step_parallel",
                    "type": "PARALLEL",
                    "parallel_tasks": [
                        {
                            "id": "task_a",
                            "type": "APPLY_PROGRAM",
                            "payload": {"program_domain": "shareasale.com", "id": "A"}
                        },
                        {
                            "id": "task_b",
                            "type": "APPLY_PROGRAM",
                            "payload": {"program_domain": "shareasale.com", "id": "B"}
                        }
                    ],
                    "next": "step_end"
                },
                {
                    "id": "step_end",
                    "type": "DISCOVER_PROGRAM",
                    "payload": {"query": "end"}
                }
            ]
        }
        
        wf_def = workflow_service.create_definition(
            db, 
            tenant.id, 
            f"Parallel Test {uuid.uuid4().hex[:6]}", 
            definition
        )
        print(f"Created Workflow Definition: {wf_def.id}")
        
        # Start Instance
        instance = workflow_service.start_instance(db, tenant.id, wf_def.id)
        db.commit()
        print(f"Started Instance: {instance.id}")
        
        # Complete Start Step
        step_link = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_start"
        ).first()
        
        print(f"Completing Start Step Task: {step_link.task_id}")
        update_task_status(db, step_link.task_id, TaskStatus.COMPLETED, result={"status": "started"})
        
        # Verify Fan-Out
        db.refresh(instance)
        print(f"Current Step: {instance.current_step_id}")
        
        if instance.current_step_id != "step_parallel":
             print(f"❌ FAILED: Expected step_parallel, got {instance.current_step_id}")
             return

        # Find parallel tasks
        sub_tasks = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id.in_(["task_a", "task_b"])
        ).all()
        
        if len(sub_tasks) != 2:
            print(f"❌ FAILED: Expected 2 parallel tasks, found {len(sub_tasks)}")
            return
            
        print(f"✅ SUCCESS: Fan-out created {len(sub_tasks)} tasks")
        
        task_a = next(t for t in sub_tasks if t.step_id == "task_a")
        task_b = next(t for t in sub_tasks if t.step_id == "task_b")
        
        # Complete Task A
        print(f"Completing Task A: {task_a.task_id}")
        update_task_status(db, task_a.task_id, TaskStatus.COMPLETED, result={"res": "A"})
        
        # Verify Wait (Fan-In Check 1)
        db.refresh(instance)
        
        # Check if next step created?
        step_end = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_end"
        ).first()
        
        if step_end:
             print("❌ FAILED: Proceeded to step_end before Task B finished")
             return
        print("✅ SUCCESS: Workflow waiting for Task B")
        
        # Complete Task B
        print(f"Completing Task B: {task_b.task_id}")
        update_task_status(db, task_b.task_id, TaskStatus.COMPLETED, result={"res": "B"})
        
        # Verify Proceed (Fan-In Check 2)
        step_end = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_end"
        ).first()
        
        if not step_end:
             print("❌ FAILED: Did not proceed to step_end after Task B finished")
             # Debug info
             db.refresh(instance)
             print(f"Instance Status: {instance.status}")
             print(f"Current Step: {instance.current_step_id}")
             return
             
        print("✅ SUCCESS: Fan-In complete, proceeded to step_end")
        
        # Cleanup / Complete End Step
        update_task_status(db, step_end.task_id, TaskStatus.COMPLETED, result={"res": "end"})
        db.refresh(instance)
        if instance.status == WorkflowStatus.COMPLETED:
             print("✅ SUCCESS: Workflow Completed")

if __name__ == "__main__":
    try:
        verify_parallel()
    except Exception as e:
        import traceback
        print(f"\nCRITICAL ERROR: {e}")
        print(traceback.format_exc())
