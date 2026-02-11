"""
Prometheus metrics exporter for observability.

Exposes key system metrics in Prometheus format.
"""

from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client import multiprocess, generate_latest as generate_latest_multiprocess
from app.core.logging import logger
import os

router = APIRouter(prefix="/metrics", tags=["observability"])

# Create a custom registry
registry = CollectorRegistry()

# Define metrics
task_counter = Counter(
    'affili_ai_tasks_total',
    'Total tasks created',
    ['tenant', 'type', 'status'],
    registry=registry
)

task_duration = Histogram(
    'affili_ai_task_duration_seconds',
    'Task execution time in seconds',
    ['task_type'],
    registry=registry
)

agent_health = Gauge(
    'affili_ai_agent_health',
    'Agent health score (0-100)',
    ['agent_id', 'pool'],
    registry=registry
)

rag_search_counter = Counter(
    'affili_ai_rag_searches_total',
    'Total RAG similarity searches',
    ['tenant'],
    registry=registry
)

llm_prediction_counter = Counter(
    'affili_ai_llm_predictions_total',
    'Total LLM field predictions',
    ['source', 'confidence_bucket'],
    registry=registry
)

automation_success_counter = Counter(
    'affili_ai_automation_success_total',
    'Successful automation executions',
    ['program_type'],
    registry=registry
)

automation_failure_counter = Counter(
    'affili_ai_automation_failures_total',
    'Failed automation executions',
    ['program_type', 'failure_type'],
    registry=registry
)


@router.get("/prometheus")
def prometheus_metrics():
    """
    Expose metrics in Prometheus format.
    
    Can be scraped by Prometheus server.
    """
    try:
        # Check if running in multiprocess mode
        if 'prometheus_multiproc_dir' in os.environ:
            registry_mp = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry_mp)
            metrics_output = generate_latest(registry_mp)
        else:
            metrics_output = generate_latest(registry)
        
        return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        return Response(content=b"# Error generating metrics\n", media_type=CONTENT_TYPE_LATEST)


# Helper functions to increment metrics (called from other services)

def record_task_created(tenant_id: str, task_type: str):
    """Record a task creation."""
    task_counter.labels(tenant=tenant_id[:8], type=task_type, status="created").inc()


def record_task_completed(tenant_id: str, task_type: str, duration_seconds: float):
    """Record a completed task."""
    task_counter.labels(tenant=tenant_id[:8], type=task_type, status="completed").inc()
    task_duration.labels(task_type=task_type).observe(duration_seconds)


def record_task_failed(tenant_id: str, task_type: str):
    """Record a failed task."""
    task_counter.labels(tenant=tenant_id[:8], type=task_type, status="failed").inc()


def update_agent_health(agent_id: str, pool: str, health_score: float):
    """Update agent health gauge."""
    agent_health.labels(agent_id=agent_id[:12], pool=pool).set(health_score)


def record_rag_search(tenant_id: str):
    """Record a RAG similarity search."""
    rag_search_counter.labels(tenant=tenant_id[:8]).inc()


def record_llm_prediction(source: str, confidence: float):
    """Record an LLM prediction."""
    # Bucket confidence scores
    if confidence >= 0.8:
        bucket = "high"
    elif confidence >= 0.5:
        bucket = "medium"
    else:
        bucket = "low"
    
    llm_prediction_counter.labels(source=source, confidence_bucket=bucket).inc()


def record_automation_success(program_type: str):
    """Record successful automation."""
    automation_success_counter.labels(program_type=program_type).inc()


def record_automation_failure(program_type: str, failure_type: str):
    """Record failed automation."""
    automation_failure_counter.labels(program_type=program_type, failure_type=failure_type).inc()
