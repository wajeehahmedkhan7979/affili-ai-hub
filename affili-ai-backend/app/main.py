"""
Main FastAPI application entry point.
AFFILI-AI Backend - Modular FastAPI Monolith
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import IPAllowlistMiddleware
from app.db.session import get_engine_instance
from app.db.base import Base

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
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
)

settings = get_settings()

# Create tables on startup (lazy - only when first accessed)
# Base.metadata.create_all(bind=get_engine_instance())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    # Shutdown
    logger.info("Shutting down application")


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

# Import and add agents router
from app.api.v1.agents import router as agents_router
app.include_router(agents_router, prefix="/api/v1")


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
