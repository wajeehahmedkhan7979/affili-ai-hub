"""
Agents API endpoints for reputation tracking.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import list_agents
from app.models.agent import Agent
from app.api.dependencies import verify_tenant, require_roles
from app.core.tenant import get_tenant_id
from app.models.user import UserRole
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(verify_tenant)])


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
