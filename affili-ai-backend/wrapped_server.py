#!/usr/bin/env python
"""Test app with full exception handling"""
import sys
import os
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')
os.chdir(r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')

try:
    print("=" * 60)
    print("Loading FastAPI app with exception handling...")
    print("=" * 60)
    
    from app.main import app
    print("✓ App loaded successfully\n")
    
    # Create a wrapper that catches exceptions
    original_app = app
    
    async def wrapped_app(scope, receive, send):
        """Wrap the app to catch any exceptions"""
        try:
            await original_app(scope, receive, send)
        except Exception as e:
            print(f"\n!!! CAUGHT EXCEPTION !!!")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {e}")
            print("\nFull traceback:")
            traceback.print_exc()
            print("!!!!!!!!!!!!!!!!!!!!!\n")
            
            # Send error response
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': f"Internal Server Error: {str(e)}".encode(),
            })
    
    app = wrapped_app
    
    print("Starting Uvicorn with wrapped app...")
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    
except Exception as e:
    print(f"\n!!! STARTUP ERROR !!!")
    print(f"Exception: {e}")
    traceback.print_exc()
    sys.exit(1)
