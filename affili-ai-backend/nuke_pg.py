from sqlalchemy import create_engine, text
from app.core.config import settings

def nuke_db():
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    engine = create_engine(url)
    tables = [
        'alembic_version', 'tasks', 'programs', 'applications', 'credentials', 
        'response_pool', 'tenants', 'users', 'billing_plans', 'tenant_billing', 
        'webhook_configs', 'webhook_deliveries', 'task_metrics', 'tenant_usage', 
        'policies', 'retention_rules', 'audit_logs', 'export_jobs', 'retention_policy'
    ]
    
    with engine.connect() as conn:
        for t in tables:
            print(f"Dropping {t}...")
            conn.execute(text(f'DROP TABLE IF EXISTS "{t}" CASCADE'))
        conn.commit()
    print("Database nuked.")

if __name__ == "__main__":
    nuke_db()
