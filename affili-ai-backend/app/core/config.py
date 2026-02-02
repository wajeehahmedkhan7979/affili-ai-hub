"""
Configuration management for the AFFILI-AI backend.
Loads from environment variables using pydantic-settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from urllib.parse import urlparse


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
    API_KEY_HEADER: str = "Authorization"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:nemM%3F%26%40x%24%23BG38q@db.zyhpughphtmogpedgdlq.supabase.co:5432/postgres"
    SUPABASE_URL: str = "https://zyhpughphtmogpedgdlq.supabase.co"
    SUPABASE_KEY: str = "sb_publishable_sSY_yfGaxyBR3QkZ4jwIEA_ayc1W5o4"
    SUPABASE_SERVICE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp5aHB1Z2hwaHRtb2dwZWRnZGxxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQ3MTA2NiwiZXhwIjoyMDg1MDQ3MDY2fQ.zUxKUkSla3wfV1AoJXpKCe_y9RP8qVW3-AiLSVyR_Uo"
    
    # Security
    SECRET_KEY: str = "74853367-ad6a-45f2-aa1a-4fafa5eba549"
    ALGORITHM: str = "ES256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-base64-encoded"
    
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
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database connection string format and structure.
        
        Checks:
        - Proper URI scheme (postgresql, sqlite)
        - Special characters in passwords are properly handled
        - Required connection components present
        """
        if not v:
            raise ValueError("DATABASE_URL is required")
        
        # Remove quotes if present (they're added for .env parsing)
        v = v.strip('"').strip("'")
        
        # Check for unescaped special characters that might break parsing
        problematic_chars = {
            '#': "Hash (#) in password - quote the DATABASE_URL value in .env",
            '\n': "Newline character in DATABASE_URL",
            '\r': "Carriage return in DATABASE_URL",
        }
        
        for char, hint in problematic_chars.items():
            if char in v and not (char == '#' and '://' not in v.split(char)[0]):
                # Only flag # if it's after the scheme
                if char == '#':
                    # Check if # is in the password part
                    try:
                        parsed = urlparse(v)
                        if parsed.password and '#' in parsed.password:
                            raise ValueError(
                                f"DATABASE_URL validation failed: {hint}\n"
                                f"Received: {v[:50]}...\n"
                                f"Fix: Add quotes around DATABASE_URL in .env file"
                            )
                    except Exception:
                        pass
        
        # Try to parse the URL
        try:
            parsed = urlparse(v)
            
            # Validate scheme
            if parsed.scheme not in ('postgresql', 'postgres', 'sqlite', 'sqlite+aiosqlite'):
                raise ValueError(
                    f"Invalid database scheme '{parsed.scheme}'. "
                    f"Must be 'postgresql', 'postgres', or 'sqlite'"
                )
            
            # For PostgreSQL, validate required components
            if parsed.scheme in ('postgresql', 'postgres'):
                if not parsed.hostname:
                    raise ValueError(
                        "DATABASE_URL missing hostname. "
                        f"Format: postgresql://user:password@host:port/database"
                    )
                if not parsed.username:
                    raise ValueError(
                        "DATABASE_URL missing username. "
                        f"Format: postgresql://user:password@host:port/database"
                    )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"DATABASE_URL parsing failed: {str(e)}\n"
                f"Expected format: postgresql://user:password@host:port/database"
            )
        
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Convert comma-separated strings into a list of origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Module-level settings instance for direct imports
settings = get_settings()
