"""
Enhanced structured logging with correlation IDs and JSON output.
Phase 11: Observability
"""
import logging
import sys
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

# Context variable for correlation IDs
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = correlation_id_ctx.get()
        return True


def configure_logging():
    """
    Configure structured JSON logging for production.
    
    Features:
    - JSON format for log aggregation (ELK, Datadog, etc.)
    - Correlation IDs for request tracing
    - ISO 8601 timestamps
    - Contextual fields (service, environment)
    """
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'name': 'logger',
            'levelname': 'level',
        },
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


# Get logger instance
logger = logging.getLogger('affili-ai')


# Convenience functions for structured logging
def log_task_event(event: str, task_id: str, **kwargs):
    """Log task lifecycle events."""
    logger.info(
        f"task_{event}",
        extra={
            'event_type': 'task',
            'event': event,
            'task_id': task_id,
            **kwargs
        }
    )


def log_governance_event(event: str, tenant_id: str, **kwargs):
    """Log governance events (killswitch, quota, etc.)."""
    logger.warning(
        f"governance_{event}",
        extra={
            'event_type': 'governance',
            'event': event,
            'tenant_id': tenant_id,
            **kwargs
        }
    )


def log_security_event(event: str, user_id: str = None, **kwargs):
    """Log security events (auth, RBAC, etc.)."""
    logger.warning(
        f"security_{event}",
        extra={
            'event_type': 'security',
            'event': event,
            'user_id': user_id,
            **kwargs
        }
    )


def log_performance(operation: str, duration_ms: float, **kwargs):
    """Log performance metrics."""
    logger.info(
        f"performance_{operation}",
        extra={
            'event_type': 'performance',
            'operation': operation,
            'duration_ms': duration_ms,
            **kwargs
        }
    )
