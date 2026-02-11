import urllib.request
import json

endpoints = [
    "http://localhost:8000/api/v1/health",
    "http://localhost:8000/api/v1/programs",
    "http://localhost:8000/api/v1/applications",
    "http://localhost:8000/api/v1/tasks",
    "http://localhost:8000/api/v1/audit",
    "http://localhost:8000/api/v1/agent/status",
    "http://localhost:8000/api/v1/response-pool",
    "http://localhost:8000/api/v1/dashboards/system-overview"
]

print("=== Surgical Health Check ===")
for url in endpoints:
    try:
        with urllib.request.urlopen(url) as response:
            print(f"✓ {url:60} | Status: {response.status}")
    except Exception as e:
        print(f"❌ {url:60} | Error: {e}")
        if hasattr(e, 'read'):
            print(f"   Response: {e.read().decode()}")
