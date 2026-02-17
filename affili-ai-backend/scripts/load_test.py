import concurrent.futures
import time
import uuid
import requests
import random
import statistics
from datetime import datetime

# CONFIGURATION
# Assuming backend running locally on port 8000
API_URL = "http://localhost:8000/api/v1"
CONCURRENT_USERS = 20
TASKS_PER_USER = 10
TOTAL_TASKS = CONCURRENT_USERS * TASKS_PER_USER

# AUTHENTICATION (Using dev credentials)
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password"

def get_auth_token():
    try:
        resp = requests.post(f"{API_URL}/auth/login", data={
            "username": ADMIN_EMAIL, 
            "password": ADMIN_PASSWORD
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"Login failed: {resp.text}")
        return None
    except Exception as e:
        print(f"Auth connection failed: {e}")
        return None

def submit_task(session, token, user_id):
    """Submits a single task and returns time taken to receive 201 Created."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "type": "TEST_LOAD",
        "payload": {"user": user_id, "data": uuid.uuid4().hex}
    }
    
    start_time = time.time()
    try:
        resp = session.post(f"{API_URL}/tasks/", json=payload, headers=headers)
        duration = time.time() - start_time
        
        if resp.status_code == 201:
            return ("SUCCESS", duration, resp.json()["id"])
        elif resp.status_code == 429:
            return ("RATE_LIMIT", duration, None)
        else:
            return (f"ERROR_{resp.status_code}", duration, None)
    except Exception as e:
        return (f"EXCEPTION_{str(e)}", time.time() - start_time, None)

def simulate_user(user_id, token):
    """Simulates a user submitting multiple tasks."""
    session = requests.Session()
    results = []
    
    for i in range(TASKS_PER_USER):
        res = submit_task(session, token, user_id)
        results.append(res)
        # Random think time between 0.1s and 0.5s
        time.sleep(random.uniform(0.1, 0.5))
        
    return results

def run_load_test():
    print(f"=== STARTING LOAD TEST: {TOTAL_TASKS} Tasks / {CONCURRENT_USERS} Threads ===")
    token = get_auth_token()
    if not token:
        print("CRITICAL: Cannot authenticate. Aborting.")
        return

    start_time = time.time()
    all_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = {executor.submit(simulate_user, f"user_{i}", token): i for i in range(CONCURRENT_USERS)}
        
        for future in concurrent.futures.as_completed(futures):
            user_results = future.result()
            all_results.extend(user_results)

    total_duration = time.time() - start_time
    
    # ANALYSIS
    successes = [r for r in all_results if r[0] == "SUCCESS"]
    latencies = [r[1] for r in successes]
    errors = [r for r in all_results if r[0] != "SUCCESS"]
    
    throughput_tpm = (len(successes) / total_duration) * 60
    
    print("\n=== LOAD TEST RESULTS ===")
    print(f"Total Time:       {total_duration:.2f}s")
    print(f"Total Requests:   {len(all_results)}")
    print(f"Successful Tasks: {len(successes)} ({len(successes)/TOTAL_TASKS*100:.1f}%)")
    print(f"Failed Tasks:     {len(errors)}")
    
    if errors:
        print("Error Breakdown:")
        err_counts = {}
        for e in errors:
            err_counts[e[0]] = err_counts.get(e[0], 0) + 1
        for k, v in err_counts.items():
            print(f"  - {k}: {v}")

    print(f"\nThroughput:       {throughput_tpm:.0f} tasks/min")
    
    if latencies:
        print(f"Avg Latency:      {statistics.mean(latencies)*1000:.0f} ms")
        print(f"P95 Latency:      {statistics.quantiles(latencies, n=20)[18]*1000:.0f} ms") # Approx P95
        print(f"Max Latency:      {max(latencies)*1000:.0f} ms")
    
    print("=========================")

if __name__ == "__main__":
    run_load_test()
