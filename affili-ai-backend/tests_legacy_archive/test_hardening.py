import httpx
import uuid
import time
import sys
import unittest

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test-api-key"  # Adjust if needed, but existing tests use this

class TestHardening(unittest.TestCase):
    def setUp(self):
        self.headers = {"Authorization": f"Bearer {API_KEY}"}
        
    def create_task(self):
        task_data = {
            "task_type": "APPLY_PROGRAM",
            "payload": {
                "program_name": "Test Program",
                "email": "test@example.com",
                "name": "Test User",
                "website": "example.com"
            }
        }
        resp = httpx.post(f"{BASE_URL}/api/v1/tasks", json=task_data, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        return resp.json()["id"]
        
    def test_heartbeat_and_cleanup(self):
        print("\n[Test] Creating task...")
        task_id = self.create_task()
        print(f"[Test] Task created: {task_id}")
        
        # 1. Claim task
        print("[Test] Claiming task...")
        claim_resp = httpx.post(
            f"{BASE_URL}/api/v1/tasks/{task_id}/claim",
            json={"agent_id": "test-agent"},
            headers=self.headers
        )
        self.assertEqual(claim_resp.status_code, 200)
        task = claim_resp.json()
        self.assertEqual(task["status"], "CLAIMED")
        
        # Update to RUNNING
        print("[Test] Updating to RUNNING...")
        httpx.post(
            f"{BASE_URL}/api/v1/tasks/{task_id}/update",
            json={"status": "RUNNING", "logs": "Started"},
            headers=self.headers
        )
        
        # 2. Send Heartbeat
        print("[Test] Sending Heartbeat...")
        hb_resp = httpx.post(
            f"{BASE_URL}/api/v1/tasks/{task_id}/heartbeat",
            headers=self.headers
        )
        self.assertEqual(hb_resp.status_code, 200)
        
        # Verify in DB (GET task)
        task_resp = httpx.get(f"{BASE_URL}/api/v1/tasks/{task_id}", headers=self.headers)
        task = task_resp.json()
        print(f"[Test] Last Heartbeat: {task.get('last_heartbeat')}")
        self.assertIsNotNone(task.get("last_heartbeat"))
        
        # 3. Test Cleanup (Timeout)
        # Since we can't easily mock time in the backend from here without messing with the DB directly or waiting,
        # we will use a small timeout for the cleanup function via the API argument.
        
        # Wait 2 seconds
        time.sleep(2)
        
        # Call cleanup with timeout_seconds=1 (so our 2s old heartbeat is considered stale)
        print("[Test] Triggering Cleanup with 1s timeout...")
        cleanup_resp = httpx.post(
            f"{BASE_URL}/api/v1/tasks/cleanup?timeout_seconds=1",
            headers=self.headers
        )
        self.assertEqual(cleanup_resp.status_code, 200)
        released = cleanup_resp.json()["released_count"]
        print(f"[Test] Released count: {released}")
        self.assertTrue(released >= 1)
        
        # Verify task is PENDING again
        task_resp = httpx.get(f"{BASE_URL}/api/v1/tasks/{task_id}", headers=self.headers)
        task = task_resp.json()
        self.assertEqual(task["status"], "PENDING")
        self.assertIsNone(task["agent_id"])
        print("[Test] Task successfully released to PENDING.")

if __name__ == "__main__":
    unittest.main()
