"""
Concurrency validation script for testing FOR UPDATE SKIP LOCKED.

This script creates multiple concurrent agents attempting to claim the same task
to prove that the atomic task claiming mechanism prevents double-execution.

Expected result: Exactly 1 agent succeeds, all others get 409 Conflict.
"""

import asyncio
import httpx
import os
from datetime import datetime
from typing import List, Tuple

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-key-placeholder")
NUM_AGENTS = 10


async def create_test_task(client: httpx.AsyncClient) -> str:
    """Create a single test task."""
    response = await client.post(
        f"{API_BASE_URL}/api/v1/tasks",
        json={
            "task_type": "DISCOVER_PROGRAM",
            "payload": {"seed_url": "https://example.com"},
            "agent_pool": "default"
        },
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    response.raise_for_status()
    task_data = response.json()
    return task_data["id"]


async def claim_task(client: httpx.AsyncClient, task_id: str, agent_id: str) -> Tuple[int, dict]:
    """Attempt to claim a task."""
    try:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/tasks/{task_id}/claim",
            json={"agent_id": agent_id, "agent_pool": "default"},
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5.0
        )
        return response.status_code, response.json() if response.status_code == 200 else {}
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {}
    except Exception as e:
        return 0, {"error": str(e)}


async def test_concurrent_claims():
    """Test concurrent task claims."""
    print("=" * 80)
    print("CONCURRENCY VALIDATION TEST")
    print("=" * 80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Number of concurrent agents: {NUM_AGENTS}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create a single task
        print("[1/3] Creating test task...")
        try:
            task_id = await create_test_task(client)
            print(f"✓ Task created: {task_id}")
        except Exception as e:
            print(f"✗ Failed to create task: {e}")
            return
        
        print()
        
        # Step 2: Spawn concurrent claim attempts
        print(f"[2/3] Spawning {NUM_AGENTS} concurrent claim attempts...")
        agent_ids = [f"agent-{i:03d}" for i in range(NUM_AGENTS)]
        
        # Launch all claim attempts simultaneously
        claim_tasks = [
            claim_task(client, task_id, agent_id)
            for agent_id in agent_ids
        ]
        
        results = await asyncio.gather(*claim_tasks)
        
        print()
        
        # Step 3: Analyze results
        print("[3/3] Analyzing results...")
        print()
        
        successes = [r for r in results if r[0] == 200]
        conflicts = [r for r in results if r[0] == 409]
        errors = [r for r in results if r[0] not in [200, 409]]
        
        print(f"Success (200):    {len(successes)} agent(s)")
        print(f"Conflict (409):   {len(conflicts)} agent(s)")
        print(f"Other errors:     {len(errors)} agent(s)")
        print()
        
        # Validation
        if len(successes) == 1 and len(conflicts) == (NUM_AGENTS - 1):
            print("✅ VALIDATION PASSED")
            print("   - Exactly 1 agent succeeded")
            print("   - All other agents received 409 Conflict")
            print("   - FOR UPDATE SKIP LOCKED is working correctly")
            print()
            
            # Show which agent won
            winner = successes[0]
            winner_agent_id = winner[1].get("agent_id", "unknown")
            print(f"   Winner: {winner_agent_id}")
            
            return True
        else:
            print("❌ VALIDATION FAILED")
            print(f"   - Expected 1 success, got {len(successes)}")
            print(f"   - Expected {NUM_AGENTS - 1} conflicts, got {len(conflicts)}")
            print()
            
            if len(successes) > 1:
                print("   ⚠️ CRITICAL: Multiple agents claimed the same task!")
                print("   This indicates a race condition in task claiming.")
            
            # Show detailed results
            print("   Detailed results:")
            for i, (status, data) in enumerate(results):
                agent_id = agent_ids[i]
                print(f"     {agent_id}: HTTP {status}")
            
            return False


async def test_find_and_claim():
    """Test the find_and_claim_task endpoint (FOR UPDATE SKIP LOCKED)."""
    print("=" * 80)
    print("FIND_AND_CLAIM TEST (FOR UPDATE SKIP LOCKED)")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient() as client:
        # Create 5 tasks
        print("[1/2] Creating 5 test tasks...")
        task_ids = []
        for i in range(5):
            try:
                task_id = await create_test_task(client)
                task_ids.append(task_id)
                print(f"  ✓ Task {i+1}: {task_id}")
            except Exception as e:
                print(f"  ✗ Failed to create task {i+1}: {e}")
        
        print()
        
        # Spawn 10 agents using find_and_claim
        print(f"[2/2] {NUM_AGENTS} agents calling /claim-next concurrently...")
        agent_ids = [f"agent-find-{i:03d}" for i in range(NUM_AGENTS)]
        
        async def find_and_claim(agent_id: str):
            try:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/tasks/claim-next",
                    json={"agent_id": agent_id, "agent_pool": "default"},
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return (200, data.get("id") if data else None)
                else:
                    return (response.status_code, None)
            except Exception as e:
                return (0, str(e))
        
        claim_tasks = [find_and_claim(agent_id) for agent_id in agent_ids]
        results = await asyncio.gather(*claim_tasks)
        
        print()
        
        # Analyze
        claimed_tasks = [r[1] for r in results if r[0] == 200 and r[1]]
        unique_claimed = set(claimed_tasks)
        
        print(f"Total claims: {len(claimed_tasks)}")
        print(f"Unique tasks claimed: {len(unique_claimed)}")
        print()
        
        if len(claimed_tasks) == len(unique_claimed) == min(5, NUM_AGENTS):
            print("✅ FIND_AND_CLAIM VALIDATION PASSED")
            print("   - Each task claimed exactly once")
            print("   - No duplicate claims detected")
            print("   - FOR UPDATE SKIP LOCKED working correctly")
            return True
        else:
            print("❌ FIND_AND_CLAIM VALIDATION FAILED")
            if len(claimed_tasks) != len(unique_claimed):
                print(f"   ⚠️ CRITICAL: Duplicate claims detected!")
                print(f"   Total claims: {len(claimed_tasks)}, Unique: {len(unique_claimed)}")
            return False


async def main():
    """Run all concurrency validation tests."""
    print()
    print("🔬 AFFILI-AI CONCURRENCY VALIDATION SUITE")
    print()
    
    # Test 1: Direct claim endpoint
    test1_passed = await test_concurrent_claims()
    
    print()
    print("-" * 80)
    print()
    
    # Test 2: Find-and-claim endpoint
    test2_passed = await test_find_and_claim()
    
    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Test 1 (Concurrent Claims): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Find and Claim):    {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print()
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED - Concurrency safety validated!")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED - Review implementation")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
