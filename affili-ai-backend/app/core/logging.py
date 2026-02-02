import logging
import sys
import json
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar
from app.core.config import get_settings

settings = get_settings()

# Context Var for correlation ID tracking
correlation_id_ctx = ContextVar("correlation_id", default="-")

class CorrelationIdFilter(logging.Filter):
    """Filter to inject correlation ID into log records."""
    def filter(self, record):
        record.correlation_id = correlation_id_ctx.get("-")
        return True

def setup_logging():
    """Configure application-wide JSON logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    
    # Define JSON formatter with custom fields
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(levelname)s %(name)s %(message)s %(correlation_id)s %(module)s %(funcName)s',
        timestamp=True
    )
    handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Reset handlers
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    # Add correlation filter
    root_logger.addFilter(CorrelationIdFilter())
    
    # Mute some noisy loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logging.getLogger("affili_ai")

logger = setup_logging()
