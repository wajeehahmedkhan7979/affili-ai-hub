#!/usr/bin/env python
"""
Direct request test - call app endpoints directly to see real errors
"""
import sys
import os

# Set up Python path
sys.path.insert(0, r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')
os.chdir(r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')

print("=== TESTING FASTAPI ENDPOINTS DIRECTLY ===\n")

try:
    print("1. Loading app...")
    from app.main import app
    print("   ✓ App loaded\n")
    
    print("2. Creating test dependency overrides...")
    from app.db.session import get_db
    from sqlalchemy.orm import Session
    import sqlite3
    from app.db.base import Base
    
    # Create in-memory database for testing
    print("   Creating test database connection...")
    
    # Get a real database session
    print("   ✓ Test setup ready\n")
    
    print("3. Testing health endpoint via Starlette ASG...")
    from starlette.applications import Starlette
    from starlette.testclient import TestClient as StarletteTestClient
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    
    # Create a test request
    from io import BytesIO
    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/api/health',
        'query_string': b'',
        'root_path': '',
        'scheme': 'http',
        'server': ('127.0.0.1', 8000),
        'client': ('127.0.0.1', 12345),
        'asgi': {'version': '3.0'},
        'state': {},
    }
    
    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}
    
    responses = []
    
    async def send(message):
        responses.append(message)
        print(f"   Response message: {message}")
    
    # Run the app
    import asyncio
    
    async def test_endpoint():
        print("   Calling app with test request...")
        await app(scope, receive, send)
        return responses
    
    results = asyncio.run(test_endpoint())
    print(f"   ✓ Got response: {results}\n")
    
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")
    import traceback
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
