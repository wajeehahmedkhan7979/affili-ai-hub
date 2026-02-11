from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.tenant import Tenant
from app.models.program import Program
from app.models.application import Application
from app.models.task import Task
from app.models.agent import Agent
from app.models.response_pool import ResponsePool
from app.models.form_field_embedding import FormFieldEmbedding
from app.models.metrics import TaskMetrics

print("Syncing schema (creating missing tables)...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Schema sync complete.")
except Exception as e:
    print(f"❌ Schema sync failed: {e}")
