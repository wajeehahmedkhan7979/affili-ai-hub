"""API v1 routers."""

from app.api.v1.health import router as health_router
from app.api.v1.programs import router as programs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.response_pool import router as response_pool_router
from app.api.v1.reports import router as reports_router
from app.api.v1.usage import router as usage_router
from app.api.v1.audit import router as audit_router
from app.api.v1.exports import router as exports_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.observability import router as observability_router
from app.api.v1.policies import router as policies_router
from app.api.v1.retention import router as retention_router

__all__ = [
    "health_router",
    "programs_router",
    "applications_router",
    "tasks_router",
    "response_pool_router",
    "reports_router",
    "usage_router",
    "audit_router",
    "exports_router",
    "auth_router",
    "billing_router",
    "webhooks_router",
    "observability_router",
    "policies_router",
    "retention_router",
]
