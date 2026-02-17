"""
Main FastAPI application entry point.
AFFILI-AI Backend - Modular FastAPI Monolith
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import asyncio

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import IPAllowlistMiddleware
from app.db.session import get_engine_instance
from app.db.base import Base

# Phase 11: Structured logging
from app.core import logging as app_logging
app_logging.configure_logging()
logger = app_logging.logger

# Phase 10: Tenant-aware rate limiting
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.api.v1 import (
    health_router,
    programs_router,
    applications_router,
    tasks_router,
    response_pool_router,
    reports_router,
    usage_router,
    audit_router,
    exports_router,
    auth_router,
    billing_router,
    webhooks_router,
    observability_router,
    policies_router,
    retention_router,
    dashboards_router,
    feedback_router,
    metrics_router,
    governance_router,
    operator_router,
    agents_router,
    prompts_router, # Added prompts_router
    workflows_router, # Added workflows_router
)

# Import Phase 11 health checks
from app.api.endpoints.health import router as health_check_router

settings = get_settings()

# Create tables on startup (lazy - only when first accessed)
Base.metadata.create_all(bind=get_engine_instance())


async def synthetic_operator_task():
    """Background task for periodic system certification."""
    from app.services.synthetic_operator import synthetic_op
    
    # Wait for app to be fully ready
    await asyncio.sleep(60) 
    
    while True:
        try:
            logger.info("Starting Synthetic Operator certification cycle")
            await synthetic_op.run_certification()
        except Exception as e:
            logger.error(f"Synthetic Operator background task error: {e}")
        
        # Run every 10 minutes (600 seconds)
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # DB Check
    try:
        from sqlalchemy import inspect
        from app.db.session import get_engine_instance
        engine = get_engine_instance()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Startup Table Check: {tables}")
        if 'synthetic_audits' not in tables:
            logger.warning("Table 'synthetic_audits' MISSING on startup! Attempting emergency creation...")
            from app.db.base import Base
            Base.metadata.create_all(bind=engine)
            logger.info(f"After emergency creation: {inspect(engine).get_table_names()}")
    except Exception as e:
        logger.error(f"Startup DB Check Failed: {e}")
    
    # Phase 26.3: Initialize Redis Event Bus
    from app.core.redis_bus import broadcaster
    from app.core.websockets import manager
    
    try:
        await broadcaster.connect()
        # Register the WebSocket manager to handle distributed messages
        await broadcaster.subscribe("ws:tenant:*", manager._handle_remote_message)
        await broadcaster.subscribe("ws:system:all", manager._handle_remote_message)
        # Start background listener
        await broadcaster.start_listening()
        logger.info("Redis Event Bus initialized and listening")
    except Exception as e:
        logger.error(f"Failed to initialize Redis Event Bus: {e}")
        # In a real production app, we might want to fail hard here 
        # but for dev we'll allow it to run with degraded WS features
    
    # Phase 26.4: Start Synthetic Operator
    certification_task = asyncio.create_task(synthetic_operator_task())
    
    yield
    # Shutdown
    logger.info("Shutting down application")
    certification_task.cancel()
    try:
        await broadcaster.disconnect()
    except Exception as e:
        logger.warning(f"Error during Redis Event Bus shutdown: {e}")


from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import correlation_id_ctx
import uuid

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_ctx.set(correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for automated affiliate marketing platform",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Add Middleware
app.add_middleware(CorrelationIdMiddleware)

# Phase 11: Metrics Security
if settings.METRICS_ENABLED:
    from app.core.middleware.security import MetricsSecurityMiddleware
    app.add_middleware(MetricsSecurityMiddleware)

# IP Allowlist Hardening (Configurable via settings.ALLOWED_IPS in production)
app.add_middleware(IPAllowlistMiddleware, allowlist=getattr(settings, "ALLOWED_IPS", []))

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for storage directory
storage_path = os.path.join(os.getcwd(), "storage")
os.makedirs(storage_path, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")


# Include routers
# Phase 11: Health checks (Kubernetes probes)
app.include_router(health_check_router)
# app.include_router(health_check_router) # Original line

# Phase 11: Prometheus metrics endpoint
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from app.api.endpoints import health
app.include_router(health.router, prefix="/health", tags=["health"])
# Phase 14: UX & Observability
from app.api.endpoints import websockets
app.include_router(websockets.router, tags=["websockets"])
# app.include_router(# analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(prompts_router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(health_router, prefix="/api/v1")
app.include_router(programs_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(response_pool_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1") # Added reports_router
app.include_router(usage_router, prefix="/api/v1") # Added usage_router
app.include_router(audit_router, prefix="/api/v1") # Added audit_router
app.include_router(exports_router, prefix="/api/v1") # Added exports_router
app.include_router(auth_router, prefix="/api/v1") # Added auth_router
app.include_router(billing_router, prefix="/api/v1") # Added billing_router
app.include_router(webhooks_router, prefix="/api/v1") # Added webhooks_router
app.include_router(observability_router, prefix="/api/v1") # Added observability_router
app.include_router(policies_router, prefix="/api/v1") # Added policies_router
app.include_router(retention_router, prefix="/api/v1") # Added retention_router

# Import and add RAG router (Phase H)
from app.api.v1.rag import router as rag_router
app.include_router(rag_router, prefix="/api/v1") # Added rag_router


# Add AI automation routers (Phases O-R)
app.include_router(dashboards_router, prefix="/api/v1") # Dashboard metrics
app.include_router(feedback_router, prefix="/api/v1") # Human feedback loop
app.include_router(metrics_router, prefix="/api/v1") # Prometheus metrics

# Add operational control routers (Phase S-T)
app.include_router(governance_router, prefix="/api/v1") # Kill-switch + cost control
app.include_router(operator_router, prefix="/api/v1") # Human intervention
app.include_router(agents_router, prefix="/api/v1")
app.include_router(prompts_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
