#!/usr/bin/env python
"""
Debug server launcher - starts Uvicorn with full logging and error capture
"""
import sys
import logging

# Setup logging BEFORE importing FastAPI
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, 'D:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend')

# Now import and run
from app.main import app
import uvicorn

print("=" * 60)
print("STARTING AFFILI-AI BACKEND SERVER WITH DEBUG LOGGING")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"Path: {sys.path[0]}")
print()

uvicorn.run(
    app,
    host="127.0.0.1",
    port=8000,
    log_level="debug",
)
