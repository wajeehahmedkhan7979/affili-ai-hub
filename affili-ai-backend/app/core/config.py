"""
Configuration management for the AFFILI-AI backend.
Loads from environment variables using pydantic-settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    PROJECT_NAME: str = "AFFILI-AI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_BASE_URL: str = "http://localhost:8000"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/affili_ai_db"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key"
    
    # Agent Configuration
    AGENT_API_KEY: str = "agent-secret-key"
    AGENT_CLIENT_ID: str = "default-agent"
    AGENT_POLL_INTERVAL: int = 5
    
    # LLM & Vision
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    VISION_PROVIDER: str = "stub"  # stub, gemini, openai
    
    # Storage
    STORAGE_PROVIDER: str = "local"  # local, supabase
    LOCAL_STORAGE_PATH: str = "./uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
