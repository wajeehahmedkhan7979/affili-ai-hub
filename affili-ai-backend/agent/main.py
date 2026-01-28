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
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.automation.playwright_agent import run_apply_program_automation

# Load environment variables
load_dotenv("agent_config.env")

# Configuration from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("AGENT_API_KEY", "agent-secret-key")
AGENT_CLIENT_ID = os.getenv("AGENT_CLIENT_ID", "default-agent")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

# API endpoints
POLL_ENDPOINT = f"{API_BASE_URL}/api/v1/tasks/poll"
CLAIM_ENDPOINT = "{API_BASE_URL}/api/v1/tasks/{task_id}/claim"
UPDATE_ENDPOINT = "{API_BASE_URL}/api/v1/tasks/{task_id}/update"


async def poll_tasks() -> List[Dict[str, Any]]:
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


async def run_task(task: Dict[str, Any]) -> bool:
    """Execute a single task."""
    task_id = task["id"]
    task_type = task["task_type"]
    payload = task.get("payload", {})
    
    print(f"\nProcessing task: {task_id}")
    print(f"  Type: {task_type}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    # Update to RUNNING
    await update_task(task_id, "RUNNING", logs=f"Agent starting execution\n")
    
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
            return False
        
        return True
    except Exception as e:
        print(f"Error running task: {e}")
        await update_task(
            task_id,
            "FAILED",
            error_message=str(e),
        )
        return False


async def run_discover_program(task_id: str, payload: Dict[str, Any]) -> None:
    """Execute a DISCOVER_PROGRAM task."""
    # TODO: Implement Playwright-based program discovery
    # - Launch browser
    # - Navigate to affiliate program
    # - Extract program details (commission, terms, etc.)
    # - Return structured data
    
    logs = "Discovering program...\n"
    await update_task(task_id, "RUNNING", logs=logs)
    
    # Stub: simulate work
    await asyncio.sleep(1)
    
    result = {
        "program_name": "Discovered Program",
        "commission_rate": 0.10,
        "terms": "Standard affiliate terms",
    }
    
    await update_task(task_id, "COMPLETED", result=result, logs=logs + "Program discovery completed\n")


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
            
            await update_task(
                task_id,
                "FAILED",
                error_message=error_message,
                logs=final_logs,
                screenshot_url=screenshots.get("after"),
            )
            
            print(f"❌ Task {task_id} failed: {error_message}")
    
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


if __name__ == "__main__":
    asyncio.run(agent_loop())
