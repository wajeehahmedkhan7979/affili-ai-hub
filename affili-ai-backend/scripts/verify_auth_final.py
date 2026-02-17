import requests
import time
import sys

URL = "http://127.0.0.1:8000/api/v1/auth/login"
ME_URL = "http://127.0.0.1:8000/api/v1/auth/me"

def verify():
    print("⏳ Waiting for backend to stabilize...")
    time.sleep(5)
    
    payload = {
        "email": "admin@example.com",
        "password": "password",
        "tenant_id": "00000000-0000-0000-0000-000000000000"
    }
    
    try:
        print(f"🚀 Attempting login for {payload['email']}...")
        resp = requests.post(URL, json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token: {token[:20]}...")
            
            # Verify /me endpoint
            headers = {"Authorization": f"Bearer {token}"}
            me_resp = requests.get(ME_URL, headers=headers)
            if me_resp.status_code == 200:
                print(f"✅ Profile retrieval successful: {me_resp.json().get('email')}")
                print("🏆 AUTH RECOVERY VERIFIED.")
            else:
                print(f"❌ Profile retrieval failed: {me_resp.status_code} - {me_resp.text}")
        else:
            print(f"❌ Login failed: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ Verification script error: {e}")

if __name__ == "__main__":
    verify()
