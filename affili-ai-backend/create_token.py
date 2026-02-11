import sys
import os
from datetime import timedelta, datetime, timezone
import logging
import uuid
from jose import jwt

# Add parent dir to path to import app modules
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.tenant import set_tenant_id, DEFAULT_TENANT_ID

# Hardcoded values from app/services/auth_service.py
SECRET_KEY = "DEV_SECRET_KEY_CHANGE_IN_PROD"
ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dev_user():
    db = SessionLocal()
    try:
        email = "dev@example.com"
        
        # Set tenant context to default
        set_tenant_id(DEFAULT_TENANT_ID)
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.info(f"Creating dev user: {email}")
            user = User(
                email=email,
                hashed_password="hashed_password_placeholder",
                role=UserRole.OWNER,
                is_active=True,
                tenant_id=DEFAULT_TENANT_ID
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info("Dev user already exists")
            if user.role != UserRole.OWNER:
                user.role = UserRole.OWNER
                db.commit()

        # Generate Token matching app/services/auth_service.py:create_access_token
        expire = datetime.now(timezone.utc) + timedelta(days=365)
        to_encode = {
            "sub": str(user.id),
            "tid": str(user.tenant_id),
            "role": user.role,
            "exp": expire,
            "type": "access",
            "jti": str(uuid.uuid4())
        }
        
        access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        print(f"\nTOKEN_START\n{access_token}\nTOKEN_END\n")
        with open("token.txt", "w") as f:
            f.write(access_token)
        logger.info("Token successfully written to token.txt")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_dev_user()
