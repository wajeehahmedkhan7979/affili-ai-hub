"""API v1 routers."""

from app.api.v1.health import router as health_router
from app.api.v1.programs import router as programs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.response_pool import router as response_pool_router

__all__ = [
    "health_router",
    "programs_router",
    "applications_router",
    "tasks_router",
    "response_pool_router",
]
