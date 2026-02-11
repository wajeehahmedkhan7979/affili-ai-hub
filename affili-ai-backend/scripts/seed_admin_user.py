import sys
import uuid
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_engine_instance
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash

def seed_admin():
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
        
        # 2. Ensure Admin User exists
        admin_email = "admin@example.com"
        password = "password"
        hashed_password = get_password_hash(password)
        
        user = db.query(User).filter(User.tenant_id == tenant_id, User.email == admin_email).first()
        if not user:
            print(f"Creating admin user {admin_email}...")
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=admin_email,
                hashed_password=hashed_password,
                role=UserRole.OWNER,
                is_active=True
            )
            db.add(user)
        else:
            print(f"Admin user {admin_email} already exists. Updating password and role...")
            user.hashed_password = hashed_password
            user.role = UserRole.OWNER
            user.is_active = True
            
        db.commit()
        print(f"✅ Seeding complete! Login with {admin_email} / {password}")

if __name__ == "__main__":
    seed_admin()
