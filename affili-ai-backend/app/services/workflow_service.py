"""
Workflow orchestration service for managing multi-step automations.
"""

from sqlalchemy.orm import Session
from app.core.time import utcnow
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStatus, WorkflowStepInstance
from app.models.task import Task, TaskStatus
from app.services.task_dispatcher import create_task
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class WorkflowService:
    """Orchestrator for intelligent automation workflows."""
    
    def create_definition(self, db: Session, tenant_id: uuid.UUID, name: str, definition: Dict[str, Any], description: str = None) -> WorkflowDefinition:
        """Create a new workflow blueprint."""
        workflow_def = WorkflowDefinition(
            tenant_id=tenant_id,
            name=name,
            description=description,
            definition=definition,
            is_active=True
        )
        db.add(workflow_def)
        db.commit()
        db.refresh(workflow_def)
        return workflow_def

    def start_instance(self, db: Session, tenant_id: uuid.UUID, definition_id: uuid.UUID, initial_context: Dict[str, Any] = None) -> WorkflowInstance:
        """Bootstrap a new workflow execution."""
        instance = WorkflowInstance(
            tenant_id=tenant_id,
            definition_id=definition_id,
            status=WorkflowStatus.RUNNING,
            context=initial_context or {}
        )
        db.add(instance)
        db.flush()
        
        workflow_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == definition_id).first()
        if not workflow_def:
            raise ValueError("Workflow definition not found")
            
        steps = workflow_def.definition.get("steps", [])
        if not steps:
             instance.status = WorkflowStatus.FAILED
             db.commit()
             return instance
             
        first_step = steps[0]
        self._execute_step(db, instance, first_step)
        
        db.commit()
        db.refresh(instance)
        return instance

    def handle_task_completion(self, db: Session, task_id: uuid.UUID):
        """ Progress workflow when a task reaches a terminal state."""
        # Find the step instance associated with this task
        step_instance = db.query(WorkflowStepInstance).filter(WorkflowStepInstance.task_id == task_id).first()
        if not step_instance:
            return
            
        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == step_instance.instance_id).first()
        if not instance or instance.status != WorkflowStatus.RUNNING:
            return
            
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
            
        # Update context with result
        if task.status == TaskStatus.COMPLETED and task.result:
             new_context = dict(instance.context or {})
             # If part of a parallel group, might want to namespace the result?
             # For now, just overwriting key - users should ensure unique step IDs or handle overwrites
             new_context[step_instance.step_id] = task.result
             instance.context = new_context
             db.add(instance) # Flag modified

        if task.status != TaskStatus.COMPLETED:
            # Phase 21.2: Compensation Logic
            workflow_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == instance.definition_id).first()
            current_step_def = next((s for s in workflow_def.definition.get("steps", []) if s["id"] == step_instance.step_id), None)
            
            if current_step_def and "on_failure" in current_step_def:
                failure_handler_id = current_step_def["on_failure"]
                _logger.info(f"Task {task_id} failed. Triggering compensation step: {failure_handler_id}")
                
                # Execute compensation step
                handler_step = next((s for s in workflow_def.definition.get("steps", []) if s["id"] == failure_handler_id), None)
                if handler_step:
                    self._execute_step(db, instance, handler_step)
                    db.commit()
                    return

            instance.status = WorkflowStatus.FAILED
            instance.completed_at = utcnow()
            db.commit()
            return

        # Phase 21.3: Parallel Fan-In Check
        # Check if this task was part of a parallel group. 
        # Since we don't strictly link siblings in DB, we check if the *current_step_id* of the instance 
        # refers to a PARALLEL step in the definition.
        
        workflow_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == instance.definition_id).first()
        current_node_def = next((s for s in workflow_def.definition.get("steps", []) if s["id"] == instance.current_step_id), None)

        if current_node_def and current_node_def.get("type") == "PARALLEL":
             # The instance.current_step_id points to the PARENT parallel step.
             # We need to check if ALL sub-tasks dispatched for this parallel step are complete.
             
             # Get all step instances for this workflow instance that match the sub-step IDs of the parallel group
             parallel_sub_steps = current_node_def.get("parallel_tasks", [])
             sub_step_ids = [s["id"] for s in parallel_sub_steps]
             
             # Count how many of these are complete
             # We need to find the task IDs associated with these sub-steps for THIS instance
             # Limitation: If the same step ID is reused in a loop, this simple logic might be ambiguous. 
             # Assuming unique step IDs per workflow for Phase 21.
             
             related_step_instances = db.query(WorkflowStepInstance).filter(
                 WorkflowStepInstance.instance_id == instance.id,
                 WorkflowStepInstance.step_id.in_(sub_step_ids)
             ).all()
             
             if len(related_step_instances) < len(sub_step_ids):
                  # Not all tasks even created yet? Or just one finished? 
                  # Actually _execute_step creates all of them. 
                  # So we just check if all exist and their tasks are completed.
                  pass 
             
             all_done = True
             for si in related_step_instances:
                 t = db.query(Task).filter(Task.id == si.task_id).first()
                 if not t or t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                     all_done = False
                     break
            
             if not all_done:
                 # Wait for others
                 db.commit()
                 return
                 
             # If all done, proceed from the metrics of the Parallel step itself (which is virtual) to next
             # The context has been updated by each individual task completion above.
             pass

        # If we are here, either it was a normal step, or the LAST task of a generic parallel group.
        # But wait, if it was a normal step, instance.current_step_id is THAT step.
        # If it was a parallel sub-task, what is instance.current_step_id?
        # In _execute_step for PARALLEL, we set instance.current_step_id = parallel_step["id"].
        # So the logic above holds.
        
        # However, for a NORMAL step, we need to ensure we don't get stuck if we just finished it.
        # Logic: 
        # 1. Identity current node in definition
        # 2. If PARALLEL -> check all sub-tasks. If all done -> proceed. Else -> return.
        # 3. If NORMAL -> proceed.
        
        # Refetch definition to be safe
        workflow_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == instance.definition_id).first()
        
        # Determine the ID to look up for "next". 
        # If we just finished a sub-task of a parallel step, the "current" logical step of the workflow is the Parallel Parent.
        # If we finished a normal step, it is that step.
        
        current_step_id_scope = instance.current_step_id
        
        # If the step_instance.step_id (the one that just finished) is NOT current_step_id_scope,
        # it implies we are inside a parallel group (or a sub-flow).
        
        if step_instance.step_id != current_step_id_scope:
             # We are likely in a parallel sub-task. 
             # confirmed by the logic above. 
             # If we haven't returned yet (due to not all_done), it means ALL ARE DONE.
             # So we proceed using the PARENT step's transition logic.
             pass
        else:
             # Normal step finished. Proceed.
             pass

        next_step = self._find_next_step(workflow_def, current_step_id_scope, instance.context)
        
        if next_step:
            self._execute_step(db, instance, next_step)
        else:
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = utcnow()
            
        db.commit()

    def _execute_step(self, db: Session, instance: WorkflowInstance, step_definition: Dict[str, Any]):
        """Dispatch a task (or tasks) for the specified step."""
        instance.current_step_id = step_definition["id"]
        
        if step_definition.get("type") == "PARALLEL":
             # Fan-Out
             parallel_tasks = step_definition.get("parallel_tasks", [])
             for pt in parallel_tasks:
                  # Recursively dispatch? No, create tasks directly but don't update instance.current_step_id
                  # We treat them as "child" tasks of this step.
                  
                  payload = pt.get("payload", {}).copy()
                  self._inject_context(payload, instance.context)
                  
                  # Set tenant context
                  from app.core.tenant import set_tenant_id
                  set_tenant_id(str(instance.tenant_id))
                  
                  task = create_task(
                      db,
                      task_type=pt["type"],
                      payload=payload,
                      agent_pool=pt.get("agent_pool", "default")
                  )
                  
                  step_link = WorkflowStepInstance(
                      instance_id=instance.id,
                      task_id=task.id,
                      step_id=pt["id"] # Link to the sub-step ID
                  )
                  db.add(step_link)
             
             db.flush()
             return

        # Normal Execution
        payload = step_definition.get("payload", {}).copy()
        self._inject_context(payload, instance.context)
        
        # Set tenant context for task creation
        from app.core.tenant import set_tenant_id
        set_tenant_id(str(instance.tenant_id))
        
        task = create_task(
            db,
            task_type=step_definition["type"],
            payload=payload,
            agent_pool=step_definition.get("agent_pool", "default")
        )
        
        step_link = WorkflowStepInstance(
            instance_id=instance.id,
            task_id=task.id,
            step_id=step_definition["id"]
        )
        db.add(step_link)
        db.flush()  # Ensure link is persisted immediately

    def _find_next_step(self, workflow_def: WorkflowDefinition, current_step_id: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine next step based on transitions and conditions."""
        steps = workflow_def.definition.get("steps", [])
        current_node = next((s for s in steps if s["id"] == current_step_id), None)
        if not current_node:
            return None
            
        next_id = None
        transitions = current_node.get("transitions", [])
        for trans in transitions:
             if self._evaluate_condition(trans.get("condition"), context):
                  next_id = trans["next"]
                  break
        
        if not next_id:
             next_id = current_node.get("next")
             
        if not next_id:
             return None
             
        return next((s for s in steps if s["id"] == next_id), None)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against context.
        Supports: ==, !=, >, <, >=, <=, in, not in
        Format: "key operator value" e.g. "context.step_a.success == True"
        """
        if not condition:
            return False
            
        try:
            # handle 'not in' first as it has two words for operator
            if " not in " in condition:
                operator = "not in"
            else:
                # Find the operator
                operators = ["==", "!=", ">=", "<=", ">", "<", " in "]
                operator = next((op for op in operators if op in condition), None)
                
            if not operator:
                _logger.warning(f"No valid operator found in condition: {condition}")
                return False
                
            left_str, right_str = condition.split(operator, 1)
            left_val = self._get_value_from_context(left_str.strip(), context)
            
            # Parse right side value
            right_str = right_str.strip()
            if right_str.lower() == "true":
                right_val = True
            elif right_str.lower() == "false":
                right_val = False
            elif right_str.lower() == "null" or right_str.lower() == "none":
                right_val = None
            elif right_str.isdigit():
                right_val = int(right_str)
            elif right_str.replace(".", "", 1).isdigit():
                 try:
                    right_val = float(right_str)
                 except ValueError:
                    right_val = right_str.strip("'\"")
            else:
                right_val = right_str.strip("'\"")

            # Perform comparison
            if operator == "==":
                return left_val == right_val
            elif operator == "!=":
                return left_val != right_val
            elif operator == ">":
                return left_val is not None and right_val is not None and left_val > right_val
            elif operator == "<":
                 return left_val is not None and right_val is not None and left_val < right_val
            elif operator == ">=":
                 return left_val is not None and right_val is not None and left_val >= right_val
            elif operator == "<=":
                 return left_val is not None and right_val is not None and left_val <= right_val
            elif operator.strip() == "in":
                 return right_val is not None and left_val in right_val
            elif operator == "not in":
                 return right_val is not None and left_val not in right_val
                 
            return False

        except Exception as e:
             _logger.warning(f"Condition evaluation failed: {e}")
             return False

    def _get_value_from_context(self, path: str, context: Dict[str, Any]) -> Any:
        """Extract value from context using dot notation (e.g. context.step_a.status)."""
        if not path.startswith("context."):
            return path # Request is literal? Or maybe error? Assuming literal for now if not context path
            
        parts = path.split(".")[1:]
        curr = context
        for p in parts:
            if isinstance(curr, dict):
                curr = curr.get(p)
            else:
                return None
        return curr

    def _inject_context(self, payload: Dict[str, Any], context: Dict[str, Any]):
        """Recursively inject values from context into payload."""
        for k, v in payload.items():
            if isinstance(v, str) and v.startswith("context."):
                parts = v.split(".")[1:]
                curr = context
                for p in parts:
                    if isinstance(curr, dict):
                        curr = curr.get(p, {})
                    else:
                        curr = None
                        break
                payload[k] = curr
            elif isinstance(v, dict):
                self._inject_context(v, context)

workflow_service = WorkflowService()