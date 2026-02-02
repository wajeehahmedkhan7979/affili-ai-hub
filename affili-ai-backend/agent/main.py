"""
Local agent runner for AFFILI-AI backend.
Polls the API for tasks and executes them using Playwright.
"""

import asyncio
import os
import sys
import httpx
import json
from typing import Optional, List, Dict, Any
import uuid
from typing import Dict, Any, Optional

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.automation.playwright_agent import run_apply_program_automation

# Load environment variables
from dotenv import load_dotenv
load_dotenv("agent_config.env")

# Core configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AGENT_ID = os.getenv("AGENT_ID", f"agent-{uuid.uuid4()}")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

# API endpoints
    """Poll the API for pending tasks."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"client_id": AGENT_CLIENT_ID, "capabilities": ["playwright", "discovery"]}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                POLL_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error polling tasks: {e}")
        return []


async def claim_task(task_id: str) -> bool:
    """Claim a task for this agent."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"agent_id": AGENT_CLIENT_ID}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CLAIM_ENDPOINT.format(API_BASE_URL=API_BASE_URL, task_id=task_id),
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return True
    except httpx.HTTPError as e:
        print(f"Error claiming task {task_id}: {e}")
        return False


async def update_task(
    task_id: str,
    status: str,
    logs: Optional[str] = None,
    result: Optional[Dict] = None,
    screenshot_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> bool:
    """Update task status and result."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "status": status,
        "logs": logs,
        "result": result,
        "screenshot_url": screenshot_url,
        "error_message": error_message,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                UPDATE_ENDPOINT.format(API_BASE_URL=API_BASE_URL, task_id=task_id),
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return True
    except httpx.HTTPError as e:
        print(f"Error updating task {task_id}: {e}")
        return False





async def run_discover_program(task_id: str, payload: Dict[str, Any]) -> None:
    """Execute affiliate program discovery task."""
    seed_url = payload.get("seed_url", "").strip()
    
    if not seed_url:
        await update_task(
            task_id,
            "FAILED",
            error_message="Missing seed_url in task payload",
        )
        return
    
    print(f"\n[DISCOVER_PROGRAM] Scanning {seed_url}")
    await update_task(task_id, "RUNNING", logs=f"Starting discovery for {seed_url}\n")
    
    try:
        # Import here to avoid circular dependencies
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.automation.discovery_agent import DiscoveryAgent
        from app.services.program_service import create_discovered_program
        from app.db.session import SessionLocal
        
        # Run discovery
        agent = DiscoveryAgent(headless=True, timeout=30000)
        success, discovered = await agent.discover_programs(seed_url)
        
        if not success:
            await update_task(
                task_id,
                "FAILED",
                error_message="Discovery failed - check logs",
            )
            return
        
        # Save discovered programs to database
        db = SessionLocal()
        try:
            saved_programs = []
            for program_data in discovered:
                program = create_discovered_program(
                    db=db,
                    name=program_data["name"],
                    base_url=program_data["base_url"],
                    signup_url=program_data["signup_url"],
                    confidence_score=program_data["confidence"]
                )
                saved_programs.append({
                    "id": str(program.id),
                    "name": program.name,
                    "signup_url": program.signup_url,
                    "confidence": program.confidence_score
                })
            
            # Update task with results
            result = {
                "discovered_count": len(discovered),
                "saved_count": len(saved_programs),
                "programs": saved_programs
            }
            
            logs = f"\nDiscovered {len(discovered)} programs\nSaved {len(saved_programs)} to database\n"
            
            await update_task(
                task_id,
                "COMPLETED",
                result=result,
                logs=logs
            )
            
            print(f"[DISCOVER_PROGRAM] Completed: {len(saved_programs)} programs saved")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"[DISCOVER_PROGRAM] Error: {e}")
        await update_task(
            task_id,
            "FAILED",
            error_message=f"Discovery error: {str(e)}",
        )


async def run_apply_program(task_id: str, payload: Dict[str, Any]) -> None:
    """Execute an APPLY_PROGRAM task using real Playwright automation."""
    logs = "Initializing Playwright automation for affiliate application...\n"
    await update_task(task_id, "RUNNING", logs=logs)
    
    try:
        # Run the real Playwright automation
        success, automation_result = await run_apply_program_automation(payload, task_id)
        
        if success:
            # Extract metadata
            screenshots = automation_result.get("screenshots", {})
            automation_logs = automation_result.get("logs", "")
            
            result = {
                "status": "submitted",
                "success": True,
                "program_name": payload.get("program_name", "Unknown"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "website": payload.get("website"),
                "screenshots": screenshots,
                "submitted_at": automation_result.get("submitted_at"),
            }
            
            final_logs = logs + automation_logs + "\n✅ AUTOMATION SUCCESSFUL"
            
            await update_task(
                task_id,
                "COMPLETED",
                result=result,
                logs=final_logs,
                screenshot_url=screenshots.get("after"),
            )
            
            print(f"✅ Task {task_id} completed successfully")
        else:
            # Automation failed
            error_message = automation_result.get("error", "Unknown error")
            automation_logs = automation_result.get("logs", "")
            screenshots = automation_result.get("screenshots", {})
            
            final_logs = logs + automation_logs + f"\n❌ ERROR: {error_message}"
            
            # Check if failure was due to CAPTCHA detection
            if error_message == "CAPTCHA_DETECTED":
                captcha_url = automation_result.get("captcha_url", "")
                captcha_reason = automation_result.get("captcha_reason", "")
                
                result = {
                    "paused_reason": "CAPTCHA detected",
                    "captcha_url": captcha_url,
                    "captcha_reason": captcha_reason,
                    "screenshots": screenshots,
                }
                
                final_logs += f"\n⏸️ Task paused: {captcha_reason}"
                
                await update_task(
                    task_id,
                    "PAUSED_FOR_CAPTCHA",
                    result=result,
                    logs=final_logs,
                    screenshot_url=screenshots.get("captcha"),
                )
                
                print(f"⏸️ Task {task_id} paused for CAPTCHA: {captcha_reason}")
            else:
                # Regular failure - classify and record
                from app.automation.failure_classifier import classify_failure
                
                failure_type = classify_failure(error_message, automation_logs)
                
                result = {
                    "failure_type": failure_type,
                    "error": error_message,
                }
                
                final_logs += f"\n❌ Classified as: {failure_type}"
                
                await update_task(
                    task_id,
                    "FAILED",
                    result=result,
                    error_message=error_message,
                    logs=final_logs,
                    screenshot_url=screenshots.get("after"),
                )
                
                print(f"❌ Task {task_id} failed ({failure_type}): {error_message}")
    
    except Exception as e:
        error_msg = f"Exception during automation: {str(e)}"
        final_logs = logs + error_msg
        
        await update_task(
            task_id,
            "FAILED",
            error_message=error_msg,
            logs=final_logs,
        )
        
        print(f"❌ Task {task_id} exception: {str(e)}")
        raise


async def run_publish_offer(task_id: str, payload: Dict[str, Any]) -> None:
    """Execute a PUBLISH_OFFER task."""
    # TODO: Implement offer publishing logic
    # - Format offer data
    # - Connect to content platforms
    # - Publish offer
    
    logs = "Publishing offer...\n"
    await update_task(task_id, "RUNNING", logs=logs)
    
    # Stub: simulate work
    await asyncio.sleep(1)
    
    result = {
        "status": "published",
        "offer_id": "offer-123",
    }
    
    await update_task(task_id, "COMPLETED", result=result, logs=logs + "Offer published\n")


async def agent_loop() -> None:
    """Main agent loop - continuously polls for tasks."""
    print(f"Starting agent: {AGENT_CLIENT_ID}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    while True:
        try:
            # Poll for tasks
            tasks = await poll_tasks()
            
            if tasks:
                print(f"\nFound {len(tasks)} task(s) to process")
                
                for task in tasks:
                    # Claim the task
                    if await claim_task(task["id"]):
                        # Run the task
                        await run_task(task)
                    else:
                        print(f"Failed to claim task {task['id']}")
            else:
                print(f"No tasks available. Waiting {POLL_INTERVAL}s...")
            
            # Wait before next poll
            await asyncio.sleep(POLL_INTERVAL)
            
        except Exception as e:
            print(f"Error in agent loop: {e}")
            await asyncio.sleep(POLL_INTERVAL)


HEARTBEAT_ENDPOINT = "{API_BASE_URL}/api/v1/tasks/{task_id}/heartbeat"

async def send_heartbeat(task_id: str) -> bool:
    """Send a heartbeat for a specific task."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                HEARTBEAT_ENDPOINT.format(API_BASE_URL=API_BASE_URL, task_id=task_id),
                headers=headers,
                timeout=5.0,
            )
            return response.status_code == 200
    except Exception:
        return False


async def heartbeat_loop(task_id: str, stop_event: asyncio.Event) -> None:
    """Background task to send heartbeats every 30s."""
    while not stop_event.is_set():
        await send_heartbeat(task_id)
        # Wait 30s or until stopped
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            continue
        except Exception:
            break


async def run_task(task: Dict[str, Any]) -> bool:
    """Execute a single task with heartbeat."""
    task_id = task["id"]
    task_type = task["task_type"]
    payload = task.get("payload", {})
    
    print(f"\nProcessing task: {task_id}")
    print(f"  Type: {task_type}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    # Update to RUNNING
    await update_task(task_id, "RUNNING", logs=f"Agent starting execution\n")
    
    # Start heartbeat
    stop_heartbeat = asyncio.Event()
    heartbeat_task = asyncio.create_task(heartbeat_loop(task_id, stop_heartbeat))
    
    success = False
    try:
        if task_type == "DISCOVER_PROGRAM":
            await run_discover_program(task_id, payload)
        elif task_type == "APPLY_PROGRAM":
            await run_apply_program(task_id, payload)
        elif task_type == "PUBLISH_OFFER":
            await run_publish_offer(task_id, payload)
        else:
            await update_task(
                task_id,
                "FAILED",
                error_message=f"Unknown task type: {task_type}",
            )
            success = False
            return False
        
        success = True
        return True
    except Exception as e:
        print(f"Error running task: {e}")
        await update_task(
            task_id,
            "FAILED",
            error_message=str(e),
        )
        success = False
        return False
    finally:
        # Stop heartbeat
        stop_heartbeat.set()
        await heartbeat_task


if __name__ == "__main__":
    asyncio.run(agent_loop())
