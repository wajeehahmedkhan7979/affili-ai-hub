"""
Agents API endpoints for reputation tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import list_agents
from app.models.agent import Agent
from app.api.dependencies import verify_tenant, require_roles
from app.core.tenant import get_tenant_id
from app.models.user import UserRole
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/status")
def get_agent_status(db: Session = Depends(get_db)):
    """Check if any agent has connected recently."""
    from datetime import datetime, timedelta
    from app.models.agent import Agent
    
    # Check for agents active in the last 60 seconds
    threshold = datetime.utcnow() - timedelta(seconds=60)
    any_active = db.query(Agent).filter(Agent.last_seen >= threshold).first()
    
    return {
        "connected": any_active is not None,
        "last_ping": any_active.last_seen.isoformat() if any_active else None
    }


class AgentResponse(BaseModel):
    """Agent response schema."""
    id: str
    pool: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    captcha_count: int
    timeout_count: int
    health_score: float
    last_seen: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[AgentResponse], 
            dependencies=[Depends(require_roles(UserRole.OWNER))])
def get_agents(
    pool: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all agents with health scores.
    
    Optional pool filter.
    """
    agents = list_agents(db, pool=pool)
    
    # Convert datetime to string for JSON serialization
    result = []
    for agent in agents:
        agent_dict = {
            "id": agent.id,
            "pool": agent.pool,
            "total_tasks": agent.total_tasks,
            "successful_tasks": agent.successful_tasks,
            "failed_tasks": agent.failed_tasks,
            "captcha_count": agent.captcha_count,
            "timeout_count": agent.timeout_count,
            "health_score": agent.health_score,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None
        }
        result.append(AgentResponse(**agent_dict))
    
    return result


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed stats for a specific agent (tenant-scoped)."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == get_tenant_id()
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        pool=agent.pool,
        total_tasks=agent.total_tasks,
        successful_tasks=agent.successful_tasks,
        failed_tasks=agent.failed_tasks,
        captcha_count=agent.captcha_count,
        timeout_count=agent.timeout_count,
        health_score=agent.health_score,
        last_seen=agent.last_seen.isoformat() if agent.last_seen else None
    )


# === Agent Polling ===

class AgentPollRequest(BaseModel):
    client_id: str
    capabilities: List[str] = []


@router.post("/poll")
def poll_tasks(
    payload: AgentPollRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Agent heartbeat and task polling.
    
    1. Register/Update agent heartbeat
    2. Return pending tasks
    """
    from app.core.security import verify_agent_key
    
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    from app.core.config import get_settings
    settings = get_settings()
    if not verify_agent_key(token):
        print(f"AUTH_DEBUG: Key mismatch!")
        print(f"AUTH_DEBUG: Received: '{token}'")
        print(f"AUTH_DEBUG: Expected: '{settings.AGENT_API_KEY}'")
        raise HTTPException(status_code=401, detail="Invalid API key")
    from app.services.agent_service import get_or_create_agent
    from app.models.task import Task, TaskStatus
    from datetime import datetime
    
    # 1. Update Agent Heartbeat
    agent = get_or_create_agent(db, payload.client_id, pool="default")
    agent.last_seen = datetime.utcnow()
    db.commit()
    
    # 2. Find pending tasks
    # Simple FIFO queue for now. 
    # Future: match capabilities to task types.
    tasks = db.query(Task).filter(
        Task.status == TaskStatus.PENDING,
        Task.agent_id.is_(None)  # Only unassigned tasks
    ).order_by(Task.created_at.asc()).limit(5).all()
    
    result = []
    for task in tasks:
        result.append({
            "id": str(task.id),
            "task_type": task.task_type.value,
            "status": task.status.value,
            "payload": task.payload,
            "created_at": task.created_at.isoformat()
        })
        
    return result
