import sys
sys.path.insert(0, 'D:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend')

from fastapi.testclient import TestClient
from app.main import app

print("=== FASTAPI ENDPOINT TESTS ===\n")

client = TestClient(app)

# Test 1: Health endpoint
try:
    print("1. Testing /api/health...")
    response = client.get("/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    if response.status_code == 200:
        print("   ✓ PASSED\n")
    else:
        print(f"   ✗ FAILED: {response.text}\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")
    import traceback
    traceback.print_exc()

# Test 2: Programs list endpoint
try:
    print("2. Testing /api/v1/programs...")
    response = client.get("/api/v1/programs")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
        print("   ✓ PASSED\n")
    else:
        print(f"   ✗ FAILED: {response.text}\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")
    import traceback
    traceback.print_exc()

# Test 3: Docs endpoint
try:
    print("3. Testing /docs...")
    response = client.get("/docs")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ PASSED\n")
    else:
        print(f"   ✗ FAILED\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")

print("=== TEST COMPLETE ===")
