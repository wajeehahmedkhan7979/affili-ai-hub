"""
Main FastAPI application entry point.
AFFILI-AI Backend - Modular FastAPI Monolith
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import engine
from app.db.base import Base
from app.api.v1 import (
    health_router,
    programs_router,
    applications_router,
    tasks_router,
    response_pool_router,
)

settings = get_settings()

# Create tables on startup
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for automated affiliate marketing platform",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health_router, prefix="/api")
app.include_router(programs_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(response_pool_router, prefix="/api/v1")


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
