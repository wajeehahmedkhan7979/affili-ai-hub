#!/usr/bin/env python
"""Backend diagnostic script"""

import sys
sys.path.insert(0, 'D:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend')

print('=== IMPORT TEST ===')
try:
    from app.core.config import settings
    print('✓ Config loaded')
    print(f'  Database: {settings.DATABASE_URL}')
except Exception as e:
    print(f'✗ Config error: {e}')
    sys.exit(1)

try:
    from app.db.base import Base
    print('✓ Database Base loaded')
except Exception as e:
    print(f'✗ Database Base error: {e}')
    sys.exit(1)

try:
    from app.models.program import Program
    from app.models.application import Application
    from app.models.task import Task
    from app.models.credential import Credential
    from app.models.response_pool import ResponsePool
    print('✓ All models loaded')
except Exception as e:
    print(f'✗ Model error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.api.v1 import health_router
    print('✓ Health router loaded')
except Exception as e:
    print(f'✗ Router error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n=== ALL CHECKS PASSED ===')
print('Backend should start successfully')
