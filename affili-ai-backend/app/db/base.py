from sqlalchemy.ext.declarative import declarative_base

# Define Base first to prevent circular imports when models import it
Base = declarative_base()

# Import all models here so they are registered with Base.metadata
# and available for Alembic or Base.metadata.create_all()
from app.models.user import User
from app.models.tenant import Tenant
from app.models.application import Application
from app.models.program import Program
from app.models.task import Task
from app.models.agent import Agent
from app.models.metrics import TaskMetrics, SyntheticAudit
from app.models.usage import TenantUsage
from app.models.llm_usage_log import LLMUsageLog
from app.models.credential import Credential
from app.models.billing import BillingPlan, TenantBilling
from app.models.security import LoginHistory, RiskProfile
from app.models.audit_log import AuditLog
from app.models.policy import Policy
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStepInstance
from app.models.response_pool import ResponsePool
