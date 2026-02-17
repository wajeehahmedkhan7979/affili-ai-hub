"""
Health check and status endpoints.
"""

from fastapi import APIRouter
from app.core.time import utcnow
from app.core.config import get_settings
from datetime import datetime

router = APIRouter(tags=["health"])

settings = get_settings()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.VERSION,
        "time": utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
    }