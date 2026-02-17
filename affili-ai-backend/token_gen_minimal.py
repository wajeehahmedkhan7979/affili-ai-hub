import time
import uuid
import base64
from jose import jwt

# Constants from app/core/config.py
SECRET_KEY = "9f7a5b3c4e2d1f0a8b9c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5"
ALGORITHM = "HS256"

def generate_test_token():
    # Standard dev user context
    user_id = "31d0a7b6-0c09-44f3-832f-7e41dcc850e2"
    tenant_id = "00000000-0000-0000-0000-000000000000"
    role = "OWNER"
    
    expire = int(time.time()) + 3600 # 1 hour
    
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "role": role,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(token)
    
    with open("token_test.txt", "w") as f:
        f.write(token)

if __name__ == "__main__":
    generate_test_token()
