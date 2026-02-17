import requests
import json

def test_login():
    url = "http://localhost:8000/api/v1/auth/login"
    payload = {
        "email": "admin@example.com",
        "password": "password",
        "tenant_id": "00000000-0000-0000-0000-000000000000"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Login successful and tokens received.")
        else:
            print(f"FAILURE: Login failed with status {response.status_code}")
    except Exception as e:
        print(f"ERROR: Could not connect to backend: {e}")

if __name__ == "__main__":
    test_login()
