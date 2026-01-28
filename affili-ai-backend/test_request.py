import requests
import sys

try:
    print("Testing http://127.0.0.1:8000/api/health...")
    response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
