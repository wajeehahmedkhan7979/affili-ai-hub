"""
Agent service for reputation tracking and health scoring.
"""

from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.task import Task
from app.automation.failure_classifier import FailureType
from datetime import datetime
from typing import Optional


from app.core.tenant import get_tenant_id

def get_or_create_agent(db: Session, agent_id: str, pool: str = "default") -> Agent:
    """
    Get existing agent or create new one (tenant-scoped).
    
    Args:
        db: Database session
        agent_id: Agent identifier
        pool: Agent pool name
        
    Returns:
        Agent object
    """
    tenant_id = get_tenant_id()
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == tenant_id
    ).first()
    
    if not agent:
        agent = Agent(id=agent_id, pool=pool, tenant_id=tenant_id)
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    return agent


def update_agent_stats(db: Session, task: Task) -> Optional[Agent]:
    """
    Update agent statistics based on task completion.
    
    Args:
        db: Database session
        task: Completed task
        
    Returns:
        Updated Agent object
    """
    if not task.agent_id:
        return None
    
    agent = get_or_create_agent(db, task.agent_id, task.agent_pool or "default")
    
    # Update counters
    agent.total_tasks += 1
    agent.last_seen = datetime.utcnow()
    
    if task.status == "COMPLETED":
        agent.successful_tasks += 1
    elif task.status == "FAILED":
        agent.failed_tasks += 1
        
        # Track specific failure types
        if task.result and isinstance(task.result, dict):
            failure_type = task.result.get("failure_type")
            if failure_type == FailureType.TIMEOUT.value:
                agent.timeout_count += 1
    elif task.status == "PAUSED_FOR_CAPTCHA":
        agent.captcha_count += 1
    
    # Recalculate health score
    agent.health_score = calculate_health_score(agent)
    
    db.commit()
    db.refresh(agent)
    
    return agent


def calculate_health_score(agent: Agent) -> float:
    """
    Calculate agent health score (0-100).
    
    Factors:
    - Success rate (60%)
    - CAPTCHA rate (20%)
    - Timeout rate (20%)
    
    Args:
        agent: Agent object
        
    Returns:
        Health score between 0 and 100
    """
    if agent.total_tasks == 0:
        return 100.0
    
    # Success rate component (60%)
    success_rate = agent.successful_tasks / agent.total_tasks
    success_score = success_rate * 60
    
    # CAPTCHA rate component (20%) - lower is better
    captcha_rate = agent.captcha_count / agent.total_tasks
    captcha_score = (1 - captcha_rate) * 20
    
    # Timeout rate component (20%) - lower is better
    timeout_rate = agent.timeout_count / agent.total_tasks
    timeout_score = (1 - timeout_rate) * 20
    
    total_score = success_score + captcha_score + timeout_score
    
    return round(min(max(total_score, 0.0), 100.0), 2)


def list_agents(db: Session, pool: Optional[str] = None):
    """
    List all agents with optional pool filter (tenant-scoped).
    
    Args:
        db: Database session
        pool: Optional pool filter
        
    Returns:
        List of Agent objects
    """
    query = db.query(Agent).filter(Agent.tenant_id == get_tenant_id())
    
    if pool:
        query = query.filter(Agent.pool == pool)
    
    return query.order_by(Agent.health_score.desc()).all()
