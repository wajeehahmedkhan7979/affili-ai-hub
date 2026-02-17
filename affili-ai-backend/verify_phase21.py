"""
Verification script for Phase 21 Workflow Orchestrator.
"""

from sqlalchemy.orm import Session
from app.db.session import get_engine_instance
from app.db.base import Base
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStatus, WorkflowStepInstance
from app.models.task import Task, TaskStatus
from app.models.tenant import Tenant
from app.services.workflow_service import workflow_service
from app.services.task_dispatcher import update_task_status
import uuid
import time

def verify_workflow_flow():
    engine = get_engine_instance()
    
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as db:
        # 1. Get a tenant ID for the test
        tenant = db.query(Tenant).first()
        if not tenant:
            print("ERROR: No tenant found in DB. Run seed_dev_user.py first.")
            return
        
        tenant_id = tenant.id
        print(f"Using Tenant: {tenant.name} ({tenant_id})")

        # 2. Define a multi-step workflow
        print("\n--- Creating Workflow Definition ---")
        definition = {
            "steps": [
                {
                    "id": "step_a",
                    "type": "DISCOVER_PROGRAM",
                    "payload": {"query": "test query"},
                    "next": "step_b"
                },
                {
                    "id": "step_b",
                    "type": "APPLY_PROGRAM",
                    "payload": {
                        "program_data": "context.step_a.found_programs",
                        "program_domain": "shareasale.com"  # Whitelisted domain for policy check
                    },
                }
            ]
        }
        
        wf_def = workflow_service.create_definition(
            db, 
            tenant_id, 
            "Test Sequential Workflow", 
            definition, 
            "Verification workflow"
        )
        print(f"Created Definition: {wf_def.id}")

        # 3. Start Workflow Instance
        print("\n--- Starting Workflow Instance ---")
        instance = workflow_service.start_instance(db, tenant_id, wf_def.id)
        print(f"Started Instance: {instance.id}, Status: {instance.status}, Current Step: {instance.current_step_id}")

        # 4. Verify Task Creation for Step A
        print("\n--- Verifying Step A Task ---")
        step_a_link = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_a"
        ).first()
        
        if not step_a_link:
            print("FAILED: Step A task not found.")
            return
            
        task_a = db.query(Task).filter(Task.id == step_a_link.task_id).first()
        print(f"Step A Task ID: {task_a.id}, Status: {task_a.status}")
        
        # 5. Simulate Task A Completion
        print("\n--- Simulating Step A Completion ---")
        mock_result = {"found_programs": ["program_123"]}
        update_task_status(db, task_a.id, TaskStatus.COMPLETED, result=mock_result)
        
        # 6. Verify Progression to Step B
        db.refresh(instance)
        print(f"Instance Status after Step A: {instance.status}, Current Step: {instance.current_step_id}")
        
        if instance.current_step_id != "step_b":
             print(f"FAILED: Workflow did not advance to step_b. Current: {instance.current_step_id}")
             return
             
        step_b_link = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_b"
        ).first()
        
        if not step_b_link:
             print("FAILED: Step B task link not found.")
             return
             
        task_b = db.query(Task).filter(Task.id == step_b_link.task_id).first()
        print(f"Step B Task ID: {task_b.id}, Payload: {task_b.payload}")
        
        # Verify Context Injection
        if task_b.payload.get("program_data") == ["program_123"]:
             print("✅ Context Injection SUCCESS: Step B received results from Step A.")
        else:
             print(f"FAILED: Context injection failed. Payload: {task_b.payload}")
             return

        # 7. Complete Step B and Verify Workflow Completion
        print("\n--- Simulating Step B Completion ---")
        update_task_status(db, task_b.id, TaskStatus.COMPLETED, result={"success": True})
        
        db.refresh(instance)
        print(f"Final Instance Status: {instance.status}")
        
        if instance.status == WorkflowStatus.COMPLETED:
             print("\n✅ Verification SUCCESS: Full multi-step workflow orchestrated correctly!")
        else:
             print(f"\nFAILED: Workflow did not reach COMPLETED. Status: {instance.status}")

if __name__ == "__main__":
    verify_workflow_flow()
