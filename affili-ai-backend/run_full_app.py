#!/usr/bin/env python
"""Test if app.main imports and loads correctly"""
import sys
sys.path.insert(0, r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')

print("=" * 60)
print("TESTING APP.MAIN IMPORT AND INITIALIZATION")
print("=" * 60)

try:
    print("\n1. Importing app.main...")
    from app.main import app
    print("✓ Success")
    
    print("\n2. Checking routes...")
    print(f"✓ {len(app.routes)} routes registered")
    
    print("\n3. Starting Uvicorn in RELOAD mode...")
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=9004,
        reload=False,  # Disable reload to avoid subprocess issues
        log_level="debug",
    )
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
