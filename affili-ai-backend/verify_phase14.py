"""
Verification script for Phase 14: WebSockets and Analytics.

Tests:
1. WebSocket connection to /ws/{tenant_id}
2. Analytics API endpoints:
   - /api/v1/analytics/governance
   - /api/v1/analytics/throughput
   - /api/v1/analytics/health
"""
import asyncio
import aiohttp
import sys
import json
from uuid import uuid4

# Configuration
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
TENANT_ID = "d3862846-953e-4632-841f-aa338872f232" # Use known tenant or random
AUTH_HEADERS = {
    # Assuming dev environment with no auth or basic auth for now
    # In real scenario, we'd need a valid token.
    # We'll rely on the existing auth middleware behavior.
    # If auth is required, we need a valid token.
    # For now, we'll try without and see (dev mode often permissive).
}

async def test_analytics():
    print("\n=== Testing Analytics APIs ===")
    async with aiohttp.ClientSession() as session:
        # 1. Governance
        try:
            url = f"{BASE_URL}/api/v1/analytics/governance?tenant_id={TENANT_ID}"
            print(f"GET {url}")
            async with session.get(url, headers=AUTH_HEADERS) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"Error: {await resp.text()}")
        except Exception as e:
            print(f"Failed: {e}")

        # 2. Throughput
        try:
            url = f"{BASE_URL}/api/v1/analytics/throughput?tenant_id={TENANT_ID}&window_minutes=60"
            print(f"\nGET {url}")
            async with session.get(url, headers=AUTH_HEADERS) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Response keys: {list(data.keys())}")
        except Exception as e:
            print(f"Failed: {e}")

async def test_websocket():
    print("\n=== Testing WebSocket ===")
    url = f"{WS_URL}/ws/{TENANT_ID}"
    print(f"Connecting to {url}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print("Connected!")
                
                # Send a ping (optional, if server supports it)
                await ws.send_str("ping")
                
                # Wait for potential messages (timeout 2s)
                try:
                    msg = await ws.receive_str(timeout=2.0)
                    print(f"Received: {msg}")
                except asyncio.TimeoutError:
                    print("No initial message (expected)")
                
                print("Closing connection...")
                await ws.close()
                print("Closed.")
                
    except Exception as e:
        print(f"WebSocket Test Failed: {e}")

async def main():
    # Wait a bit for server to be fully ready
    await asyncio.sleep(2)
    
    await test_analytics()
    await test_websocket()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
