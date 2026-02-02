#!/usr/bin/env python
import sys
sys.path.insert(0, r'D:\PROJECTS-REPOS\AFFILIATE-PROJ\affili-ai-hub\affili-ai-backend')

from app.core.config import get_settings
settings = get_settings()

print("Current DATABASE_URL:", settings.DATABASE_URL)
print("Current DEBUG:", settings.DEBUG)
print("Current ENVIRONMENT:", settings.ENVIRONMENT)
