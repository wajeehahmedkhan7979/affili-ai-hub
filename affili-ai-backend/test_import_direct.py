import sys
sys.path.insert(0, 'D:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend')

print("Step 1: Importing app.main...")
try:
    from app.main import app
    print("✓ app.main imported successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Checking app routes...")
try:
    routes = app.routes
    print(f"✓ Found {len(routes)} routes:")
    for route in routes:
        if hasattr(route, 'path'):
            print(f"  - {route.path} ({getattr(route, 'methods', [])})")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 3: Checking get_settings()...")
try:
    from app.core.config import get_settings
    settings = get_settings()
    print(f"✓ Settings loaded: {settings.PROJECT_NAME}")
    print(f"  DATABASE_URL: {settings.DATABASE_URL[:50]}...")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Checking database session...")
try:
    from app.db.session import get_db, get_engine_instance
    print(f"✓ Database session functions loaded")
    
    # Test engine creation
    engine = get_engine_instance()
    print(f"✓ Engine created: {type(engine)}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 5: Testing simple endpoint call...")
try:
    # Create a dummy request
    from starlette.requests import Request
    from starlette.datastructures import Headers
    
    # Call health check directly
    from app.api.v1.health import health_check
    result = health_check()
    print(f"✓ Health check direct call result: {result}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DIAGNOSTIC COMPLETE ===")
