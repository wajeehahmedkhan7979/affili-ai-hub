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
from app.api.v1.rag import router as rag_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.governance import router as governance_router
from app.api.v1.operator import router as operator_router
from app.api.v1.agents import router as agents_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.workflows import router as workflows_router

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
    "rag_router",
    "dashboards_router",
    "feedback_router",
    "metrics_router",
    "governance_router",
    "operator_router",
    "agents_router",
    "prompts_router",
]
