import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import User
from app.db.session import SessionLocal

def debug_user():
    print("DEBUG: in debug_user")
    print(f"User class: {User}")
    print(f"User class attributes: {dir(User)}")
    
    if hasattr(User, 'role'):
        print("✅ User class has 'role' attribute")
    else:
        print("❌ User class MISSING 'role' attribute")

    try:
        db = SessionLocal()
        print("Checking DB connection...")
        user = db.query(User).first()
        if user:
            print(f"Found user: {user.email}")
            print(f"User instance type: {type(user)}")
            print(f"User instance attributes: {user.__dict__}")
            try:
                print(f"User role value: {user.role}")
                print("✅ Instance role access SUCCESS")
            except AttributeError as e:
                print(f"❌ Instance role access FAILED: {e}")
        else:
            print("⚠️ No user found in DB")
        db.close()
    except Exception as e:
        print(f"❌ Error during DB check: {e}")

if __name__ == "__main__":
    debug_user()
