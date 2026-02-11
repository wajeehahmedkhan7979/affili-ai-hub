import sys
import os
from sqlalchemy import text
from app.models.user import User, UserRole
from app.db.session import SessionLocal

def test_user_model():
    print("START DEBUG USER")
    try:
        user = User(email="test@example.com", role=UserRole.ADMIN.value)
        print(f"User.role: {user.role}") 
    except Exception as e:
        print(f"Instantiation FAIL: {e}")

    db = SessionLocal()
    try:
        # Check column
        stmt = text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='role'")
        res = db.execute(stmt).scalar()
        print(f"DB 'role' column: {'FOUND' if res else 'MISSING'}")
        
    except Exception as e:
        print(f"DB FAIL: {e}")
    finally:
        db.close()
    print("END DEBUG USER")

if __name__ == "__main__":
    test_user_model()
