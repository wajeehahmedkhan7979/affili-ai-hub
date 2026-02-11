"""
Health check endpoints for production readiness.

Provides Kubernetes-compatible probes:
- Liveness: Process is alive and responding
- Readiness: Service is ready to accept traffic
- Startup: Service has completed initialization
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
import logging

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/liveness")
async def liveness():
    """
    Liveness probe: Check if the process is alive.
    
    Returns 200 if the application process is running.
    Kubernetes will restart the pod if this fails.
    
    Returns:
        dict: Service name and status
    """
    return {
        "status": "ok",
        "service": "affili-ai-backend",
        "version": "1.1.0"
    }


@router.get("/readiness")
async def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe: Check if service is ready to accept traffic.
    
    Verifies:
    - Database connection is healthy
    - Critical dependencies are available
    
    Kubernetes will remove pod from service if this fails.
    
    Returns:
        dict: Readiness status and component checks
    
    Raises:
        HTTPException: 503 if not ready
    """
    checks = {}
    is_ready = True
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {str(e)}"
        is_ready = False
        logger.error(f"Database health check failed: {e}")
    
    # Add more dependency checks here as needed:
    # - Redis connection
    # - External API health
    # - File system access
    
    if is_ready:
        return {
            "status": "ready",
            "checks": checks
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks
            }
        )


@router.get("/startup")
async def startup(db: Session = Depends(get_db)):
    """
    Startup probe: Check if service has completed initialization.
    
    Verifies:
    - Database is accessible
    - Migrations are complete (checks alembic_version table)
    
    Kubernetes will wait for this before sending traffic.
    More lenient than readiness (allows longer startup time).
    
    Returns:
        dict: Startup status
    
    Raises:
        HTTPException: 503 if still starting up
    """
    checks = {}
    is_started = True
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {str(e)}"
        is_started = False
        logger.error(f"Database connection failed during startup: {e}")
    
    # Check migrations are complete
    try:
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        if current_version:
            checks["migrations"] = "complete"
        else:
            checks["migrations"] = "no version found"
            is_started = False
    except Exception as e:
        checks["migrations"] = f"failed: {str(e)}"
        is_started = False
        logger.error(f"Migration check failed: {e}")
    
    if is_started:
        return {
            "status": "started",
            "checks": checks
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "starting",
                "checks": checks
            }
        )
