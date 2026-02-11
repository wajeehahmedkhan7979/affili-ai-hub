"""
Cardinality-controlled Prometheus metrics.
Phase 11: Observability - Cardinality Fix

CRITICAL: Unbounded cardinality breaks Prometheus.
This module provides enum-constrained versions of metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from enum import Enum
from functools import wraps
import time


# Application info
app_info = Info('affili_ai_app', 'Application information')
app_info.info({
    'version': '1.1.0',
    'environment': 'production'
})


# Reason enums for bounded cardinality
class KillSwitchReason(str, Enum):
    COST_EXCEEDED = "cost_exceeded"
    MANUAL = "manual"
    POLICY_VIOLATION = "policy_violation"
    SPAM_DETECTED = "spam_detected"
    OTHER = "other"


class QuotaType(str, Enum):
    MONTHLY_COST = "monthly_cost"
    DAILY_TASKS = "daily_tasks"
    CONCURRENT_TASKS = "concurrent_tasks"


# Task metrics (no tenant_id label for cardinality control)
tasks_created_total = Counter(
    'tasks_created_total',
    'Total number of tasks created',
    ['task_type']  # Removed tenant_id
)

tasks_claimed_total = Counter(
    'tasks_claimed_total',
    'Total number of tasks claimed by agents',
    ['agent_pool']  # Removed tenant_id
)

tasks_completed_total = Counter(
    'tasks_completed_total',
    'Total number of tasks completed',
    ['task_type', 'status']  # Removed tenant_id
)

task_claim_duration_seconds = Histogram(
    'task_claim_duration_seconds',
    'Time to claim a task from the queue',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

task_execution_duration_seconds = Histogram(
    'task_execution_duration_seconds',
    'Time to execute a task',
    ['task_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)


# Queue metrics (aggregated across all tenants)
pending_tasks_gauge = Gauge(
    'pending_tasks_total',
    'Total number of pending tasks across all tenants'
)

claimed_tasks_gauge = Gauge(
    'claimed_tasks_total',
    'Total number of claimed tasks across all tenants'
)


# Concurrency & resilience metrics
deadlock_retries_total = Counter(
    'deadlock_retries_total',
    'Number of deadlock retry attempts',
    ['function']  # Bounded: only a few functions use this
)

stale_claims_reaped_total = Counter(
    'stale_claims_reaped_total',
    'Number of stale task claims recovered by reaper'
)

heartbeat_reaper_runs_total = Counter(
    'heartbeat_reaper_runs_total',
    'Number of heartbeat reaper executions'
)


# Governance metrics (enum-constrained)
killswitch_activations_total = Counter(
    'killswitch_activations_total',
    'Number of kill-switch activations',
    ['reason']  # ENUM ONLY: KillSwitchReason
)

quota_exceeded_total = Counter(
    'quota_exceeded_total',
    'Number of quota exceeded events',
    ['quota_type']  # ENUM ONLY: QuotaType
)

killswitch_active_count = Gauge(
    'killswitch_active_count',
    'Number of tenants with active kill-switch'
)


# API metrics (endpoint label bounded to route patterns, not dynamic)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'route_pattern', 'status_code']  # route_pattern, not endpoint
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'route_pattern'],  # route_pattern, not endpoint
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)


# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],  # Bounded: claim, create, update, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_in_use = Gauge(
    'db_connection_pool_in_use',
    'Database connections currently in use'
)


# Security metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['result']  # success, failed_password, failed_user_not_found
)

rbac_denials_total = Counter(
    'rbac_denials_total',
    'RBAC permission denials',
    ['permission']  # Bounded: defined in PERMISSIONS dict
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Rate limit violations',
    ['route_pattern']  # Not free-form endpoint
)


# Helper to record killswitch with enum validation
def record_killswitch_activation(reason: str):
    """
    Record killswitch activation with enum validation.
    
    CRITICAL: Prevents unbounded cardinality from free-text reasons.
    """
    try:
        validated_reason = KillSwitchReason(reason.lower())
    except ValueError:
        validated_reason = KillSwitchReason.OTHER
    
    killswitch_activations_total.labels(reason=validated_reason.value).inc()


# Helper to record quota exceeded
def record_quota_exceeded(quota_type: str):
    """Record quota exceeded with enum validation."""
    try:
        validated_type = QuotaType(quota_type.lower())
    except ValueError:
        return  # Ignore unknown quota types
    
    quota_exceeded_total.labels(quota_type=validated_type.value).inc()


# Decorator for timing operations
def track_duration(metric: Histogram, *labels):
    """
    Decorator to track operation duration.
    
    Usage:
        @track_duration(task_claim_duration_seconds)
        def claim_task():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(*labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator


# Decorator for counting operations
def track_count(metric: Counter, *labels):
    """
    Decorator to count operation occurrences.
    
    Usage:
        @track_count(tasks_created_total, "discovery")
        def create_task():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if labels:
                metric.labels(*labels).inc()
            else:
                metric.inc()
            return result
        return wrapper
    return decorator
