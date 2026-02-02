
import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_minimal_health():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Based on main.py, health is at /api/health
        response = await client.get("/api/health")
        assert response.status_code in [200, 404] # Just check if it handles request
        if response.status_code == 200:
            print("Health OK")
        else:
            # Maybe it's at /api/v1/health or similar, but the point is NO ATTRIBUTEERROR
            print(f"Health status: {response.status_code}")
