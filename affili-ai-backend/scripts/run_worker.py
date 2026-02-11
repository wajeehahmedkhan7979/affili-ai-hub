import asyncio
import sys
import os
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.automation.discovery_agent import DiscoveryAgent
from app.services.program_service import create_discovered_program
from app.core.tenant import set_tenant_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LocalWorker")

async def run_worker():
    """
    Run a local worker to process DISCOVER_PROGRAM tasks.
    This bypasses the need for the Docker container during development.
    """
    logger.info("Starting Local Discovery Worker...")
    logger.info("Press Ctrl+C to stop.")
    
    agent = DiscoveryAgent(headless=True, timeout=60000)
    
    while True:
        db = SessionLocal()
        try:
            # Find next pending task
            # We filter by task_type to only pick up what we can handle
            task = db.query(Task).filter(
                Task.status == TaskStatus.PENDING,
                Task.task_type == "DISCOVER_PROGRAM"
            ).order_by(Task.created_at.asc()).first()
            
            if task:
                logger.info(f"Picked up Task ID: {task.id}")
                
                # Set tenant context for this task
                set_tenant_id(str(task.tenant_id))

                # Update Agent Heartbeat (Fixes "Disconnected" status in UI)
                try:
                    from app.models.agent import Agent
                    # Direct DB update to avoid service layer complexity in script
                    agent = db.query(Agent).filter(Agent.id == "docker-worker").first()
                    # Use default system tenant ID for the shared worker
                    default_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
                    
                    if not agent:
                        logger.info("Creating new agent record for docker-worker")
                        agent = Agent(
                            id="docker-worker",
                            tenant_id=default_tenant_id,
                            pool="default",
                            capabilities=["discovery", "browser"],
                            status="idle",
                            last_seen=datetime.utcnow()
                        )
                        db.add(agent)
                    else:
                        agent.last_seen = datetime.utcnow()
                        agent.status = "busy"
                        # Ensure tenant ID is set correctly just in case
                        agent.tenant_id = default_tenant_id
                    
                    db.commit()
                    logger.info(f"Updated heartbeat for agent: docker-worker (Tenant: {default_tenant_id})")
                except Exception as e:
                    logger.error(f"Failed to update agent heartbeat: {e}")
                    db.rollback()
                
                # Update status to RUNNING
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
                task.agent_id = "local-worker"
                db.commit()
                
                # Extract payload
                payload = task.payload or {}
                seed_url = payload.get("seed_url") or payload.get("url")
                
                if not seed_url:
                    logger.error("No seed URL provided in task payload.")
                    task.status = TaskStatus.FAILED
                    task.error_message = "No seed URL provided in task payload."
                    task.completed_at = datetime.utcnow()
                    db.commit()
                    continue
                
                logger.info(f"Processing URL: {seed_url}")
                
                # Execute Discovery
                try:
                    success, programs = await agent.discover_programs(seed_url)
                    
                    if success:
                        saved_programs = []
                        for p_data in programs:
                            saved_prog = create_discovered_program(
                                db=db,
                                name=p_data["name"],
                                base_url=p_data["base_url"],
                                signup_url=p_data["signup_url"],
                                confidence_score=p_data["confidence"]
                            )
                            # Convert to dict for result JSON
                            saved_programs.append({
                                "id": str(saved_prog.id),
                                "name": saved_prog.name,
                                "signup_url": saved_prog.signup_url
                            })
                            
                        task.status = TaskStatus.COMPLETED
                        task.result = {"programs": saved_programs, "count": len(saved_programs)}
                        task.completed_at = datetime.utcnow()
                        logger.info(f"Task Completed. Saved {len(saved_programs)} programs.")
                    else:
                        task.status = TaskStatus.FAILED
                        task.error_message = "Discovery agent returned failure."
                        task.completed_at = datetime.utcnow()
                        logger.error("Discovery agent execution failed.")
                        
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    logger.error(f"Error executing agent: {e}")
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Worker Exception: {str(e)}"
                    task.completed_at = datetime.utcnow()
                
                db.commit()
                
            else:
                # No tasks, wait
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            await asyncio.sleep(5)
        finally:
            db.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
