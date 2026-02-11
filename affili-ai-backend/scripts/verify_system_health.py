import json
import time
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "X-Tenant-ID": "00000000-0000-0000-0000-000000000000",
    "X-User-Email": "dev@example.com",
    "Content-Type": "application/json"
}

def test_endpoint(name, method, url, expected_status=200, checks=None):
    print(f"Testing {name} ({method} {url})...", end=" ")
    try:
        full_url = f"{BASE_URL}{url}"
        req = urllib.request.Request(full_url, headers=HEADERS)
        if method == "POST":
            req.method = "POST"
            # Empty body
            req.data = json.dumps({}).encode('utf-8')
        
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.getcode()
                response_body = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            status_code = e.code
            response_body = e.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"FAILED (Connection Error: {e.reason})")
            return False

        if status_code != expected_status:
            print(f"FAILED (Status: {status_code})")
            print(f"Response: {response_body}")
            return False
        
        try:
            data = json.loads(response_body)
        except:
            data = {} # Handle empty/text response
        
        if checks:
            for key, expected_type in checks.items():
                if key not in data:
                    print(f"FAILED (Missing key: {key})")
                    return False
        
        print(f"PASSED ✓")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def verify_system():
    print("=== AFFILI-AI SYSTEM HEALTH CHECK ===\n")
    
    success = True
    
    # 1. Agent Status
    success &= test_endpoint("Agent Status", "GET", "/agent/status", 200, {"connected": bool})
    
    # 2. Programs List
    success &= test_endpoint("Programs List", "GET", "/programs", 200)
    
    # 3. Applications List
    success &= test_endpoint("Applications List", "GET", "/applications", 200)
    
    # 4. Tasks List
    success &= test_endpoint("Tasks List", "GET", "/tasks", 200)
    
    # 5. Dashboard System Overview (CRITICAL FIX CHECK)
    # Expects: programsFound, pendingApprovals, applicationsSubmitted, connectedAgents
    success &= test_endpoint("Dashboard Stats", "GET", "/dashboards/system-overview", 200, {
        "programsFound": int,
        "pendingApprovals": int,
        "applicationsSubmitted": int,
        "connectedAgents": int
    })
    
    # 6. Response Pool
    success &= test_endpoint("Response Pool", "GET", "/response-pool", 200)

    # 7. Audit Log
    success &= test_endpoint("Audit Logs", "GET", "/audit", 200)

    print("\n=== VERIFICATION SUMMARY ===")
    if success:
        print("✅ ALL SYSTEMS OPERATIONAL")
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    verify_system()
