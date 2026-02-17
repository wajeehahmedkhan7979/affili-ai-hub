import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.services.auth_service import get_password_hash
import uuid

DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password"

def reseed():
    db = SessionLocal()
    try:
        # 1. Ensure Default Tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
        if not tenant:
            print(f"🏗️ Creating default tenant: {DEFAULT_TENANT_ID}")
            tenant = Tenant(
                id=DEFAULT_TENANT_ID,
                name="Default Tenant",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        else:
            print(f"✅ Default tenant already exists.")

        # 2. Ensure Admin User exists
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        hashed_pw = get_password_hash(ADMIN_PASSWORD)

        if not admin:
            print(f"👤 Creating admin user: {ADMIN_EMAIL}")
            print(f"Creating admin user: {ADMIN_EMAIL}")
            admin = User(
                id=uuid.uuid4(),
                tenant_id=DEFAULT_TENANT_ID,
                email=ADMIN_EMAIL,
                hashed_password=hashed_pw,
                role=UserRole.ADMIN.value,
                is_active=True
            )
            db.add(admin)
        else:
            print(f"Updating admin user password: {ADMIN_EMAIL}")
            admin.hashed_password = hashed_pw
            admin.tenant_id = DEFAULT_TENANT_ID # Ensure correct tenant link
            admin.is_active = True

        # 3. Fix other users with NULL passwords (optional cleanup)
        other_users = db.query(User).filter(User.hashed_password == None).all()
        for u in other_users:
            print(f"Patching user {u.email} with default password 'password'")
            u.hashed_password = hashed_pw

        db.commit()
        print("Reseed successful. You can now log in with:")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"   Tenant ID: {DEFAULT_TENANT_ID}")

    except Exception as e:
        print(f"Reseed failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reseed()
