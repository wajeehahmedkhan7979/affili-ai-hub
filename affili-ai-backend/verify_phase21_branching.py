"""
Verification script for Phase 21.2: Advanced Workflow Logic.
Tests Conditional Branching, Operators, and Compensation Logic.
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

def verify_branching():
    print("\n=== TEST 1: Conditional Branching (Numeric > Operator) ===")
    with Session(engine) as db:
        tenant = db.query(Tenant).first()
        if not tenant:
            print("ERROR: No tenant found")
            return
        
        tenant_id = str(tenant.id)
        set_tenant_id(tenant_id)
        
        # Define Workflow with Branching
        # Step A -> (if count > 5) -> Step B
        #        -> (else) -> Step C
        definition = {
            "steps": [
                {
                    "id": "step_start",
                    "type": "DISCOVER_PROGRAM",
                    "payload": {"query": "start"},
                    "transitions": [
                        {
                            "condition": "context.init.count > 5",
                            "next": "step_high"
                        }
                    ],
                    "next": "step_low" # Default path
                },
                {
                    "id": "step_high",
                    "type": "APPLY_PROGRAM", 
                    "payload": {"program_domain": "shareasale.com", "path": "HIGH_VALUE"}
                },
                {
                    "id": "step_low",
                    "type": "APPLY_PROGRAM",
                    "payload": {"program_domain": "shareasale.com", "path": "LOW_VALUE"}
                }
            ]
        }
        
        wf_def = workflow_service.create_definition(
            db, 
            tenant.id, 
            f"Branch Test {uuid.uuid4().hex[:6]}", 
            definition
        )
        print(f"Created Workflow Definition: {wf_def.id}")
        
        # Test Case A: High Value (Expect step_high)
        print("\n--- Running Case A: Count = 10 (Expect HIGH path) ---")
        instance = workflow_service.start_instance(
            db, 
            tenant.id, 
            wf_def.id, 
            initial_context={"init": {"count": 10}}
        )
        db.commit()
        
        # Complete Start Step
        step_link = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_start"
        ).first()
        
        if not step_link:
             print("FAILED: Start step not found")
             return

        print(f"Completing Start Step Task: {step_link.task_id}")
        update_task_status(db, step_link.task_id, TaskStatus.COMPLETED, result={"status": "done"})
        
        # Verify Next Step
        db.refresh(instance)
        print(f"Current Step: {instance.current_step_id}")
        if instance.current_step_id == "step_high":
            print("✅ SUCCESS: Branching logic correctly chose HIGH path (10 > 5)")
        else:
            print(f"❌ FAILED: Expected step_high, got {instance.current_step_id}")

        # Test Case B: Low Value (Expect step_low)
        print("\n--- Running Case B: Count = 3 (Expect LOW path) ---")
        instance_b = workflow_service.start_instance(
            db, 
            tenant.id, 
            wf_def.id, 
            initial_context={"init": {"count": 3}}
        )
        db.commit()
        
         # Complete Start Step
        step_link_b = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance_b.id,
            WorkflowStepInstance.step_id == "step_start"
        ).first()
        
        update_task_status(db, step_link_b.task_id, TaskStatus.COMPLETED, result={"status": "done"})
        
        db.refresh(instance_b)
        print(f"Current Step: {instance_b.current_step_id}")
        if instance_b.current_step_id == "step_low":
             print("✅ SUCCESS: Branching logic correctly chose LOW path (3 <= 5)")
        else:
             print(f"❌ FAILED: Expected step_low, got {instance_b.current_step_id}")


def verify_compensation():
    print("\n=== TEST 2: Compensation Logic (On Failure) ===")
    with Session(engine) as db:
        tenant = db.query(Tenant).first()
        tenant_id = str(tenant.id)
        set_tenant_id(tenant_id)
        
        # Define Workflow with Compensation
        # Step Fail -> Fails -> Step Recover
        definition = {
            "steps": [
                {
                    "id": "step_risky",
                    "type": "DISCOVER_PROGRAM",
                    "payload": {"query": "risky"},
                    "on_failure": "step_recover",
                    "next": "step_success"
                },
                {
                    "id": "step_recover",
                    "type": "APPLY_PROGRAM",
                    "payload": {"program_domain": "shareasale.com", "action": "ROLLBACK"}
                },
                {
                    "id": "step_success",
                    "type": "APPLY_PROGRAM", 
                    "payload": {"program_domain": "shareasale.com", "action": "NORMAL"}
                }
            ]
        }
        
        wf_def = workflow_service.create_definition(
            db, 
            tenant.id, 
            f"Comp Test {uuid.uuid4().hex[:6]}", 
            definition
        )
        
        instance = workflow_service.start_instance(db, tenant.id, wf_def.id)
        db.commit()
        
        # Check running
        step_link = db.query(WorkflowStepInstance).filter(
            WorkflowStepInstance.instance_id == instance.id,
            WorkflowStepInstance.step_id == "step_risky"
        ).first()
        print(f"Risky Task ID: {step_link.task_id}")
        
        # Fail the task
        print("Simulating Task Failure...")
        update_task_status(db, step_link.task_id, TaskStatus.FAILED, result={"error": "Boom"})
        
        # Verify Compensation triggered
        db.refresh(instance)
        print(f"Instance Status: {instance.status}")
        print(f"Current Step: {instance.current_step_id}")
        
        if instance.status == WorkflowStatus.RUNNING and instance.current_step_id == "step_recover":
             print("✅ SUCCESS: Compensation step triggered on failure")
        elif instance.status == WorkflowStatus.FAILED:
             print("❌ FAILED: Workflow failed immediately without compensation")
        else:
             print(f"❌ FAILED: Unexpected state {instance.status} / {instance.current_step_id}")

if __name__ == "__main__":
    try:
        verify_branching()
        verify_compensation()
    except Exception as e:
        import traceback
        print(f"\nCRITICAL ERROR: {e}")
        print(traceback.format_exc())
