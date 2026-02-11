"""
Performance Benchmark Suite.
Phase 17: Final Certification

Simulates load and measures latency against SLAs.
"""
import asyncio
import time
import httpx
import statistics
from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"
PREFIX = "/api/v1"
TENANT_ID = "d3862846-953e-4632-841f-aa338872f232"

async def measure_endpoint(name: str, method: str, url: str, payload=None, count=50):
    print(f"\nBenchmarking {name} ({count} reqs)...")
    latencies = []
    
    async with httpx.AsyncClient() as client:
        # Warmup
        await client.get(f"{BASE_URL}/health/liveness")
        
        start_time = time.time()
        for _ in range(count):
            req_start = time.time()
            try:
                if method == "GET":
                    resp = await client.get(url)
                elif method == "POST":
                    resp = await client.post(url, json=payload)
                
                latencies.append((time.time() - req_start) * 1000) # ms
            except Exception as e:
                print(f"Error: {e}")
                
        total_time = time.time() - start_time
        
    if not latencies:
        print("No successful requests.")
        return

    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]
    p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
    
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  Max: {max(latencies):.2f}ms")
    print(f"  RPS: {count / total_time:.2f}")

async def main():
    print("=== AFFILI-AI PERFORMANCE BENCHMARK ===")
    
    # 1. Health Check (Baseline)
    await measure_endpoint("Health Check", "GET", f"{BASE_URL}/health/liveness", count=100)
    
    # 2. task Listing (Read Heavy)
    await measure_endpoint("Task List", "GET", f"{BASE_URL}{PREFIX}/tasks?tenant_id={TENANT_ID}", count=50)
    
    # 3. Analytics (Aggregation Heavy)
    await measure_endpoint("Analytics Throughput", "GET", f"{BASE_URL}{PREFIX}/analytics/throughput?tenant_id={TENANT_ID}", count=20)

if __name__ == "__main__":
    asyncio.run(main())
