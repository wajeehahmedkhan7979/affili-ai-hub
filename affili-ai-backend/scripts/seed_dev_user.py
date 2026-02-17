"""
Seed the default dev user and tenant for AFFILI-AI HUB.
"""
import sys
import uuid
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_engine_instance
from app.models.tenant import Tenant
from app.models.user import User, UserRole

def seed_dev():
    engine = get_engine_instance()
    with Session(engine) as db:
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        # 1. Ensure Default Tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"Creating default tenant {tenant_id}...")
            tenant = Tenant(
                id=tenant_id,
                name="Default Tenant"
            )
            db.add(tenant)
            db.flush()
        
        # 2. Ensure Dev User exists
        dev_email = "dev@example.com"
        user = db.query(User).filter(User.tenant_id == tenant_id, User.email == dev_email).first()
        if not user:
            print(f"Creating dev user {dev_email}...")
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=dev_email,
                role=UserRole.OWNER,
                is_active=True
            )
            db.add(user)
        else:
            print(f"Dev user {dev_email} already exists. Ensuring role is OWNER...")
            user.role = UserRole.OWNER
            user.is_active = True
            
        db.commit()
        print("✅ Seeding complete!")

if __name__ == "__main__":
    seed_dev()
