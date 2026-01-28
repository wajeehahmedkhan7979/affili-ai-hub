#!/usr/bin/env python
"""Detailed server with exit code tracking"""
import sys
import os

from fastapi import FastAPI
app = FastAPI()

@app.get("/test")
def test():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    print("Server starting on port 9003...", flush=True)
    try:
        uvicorn.run(app, host="127.0.0.1", port=9003)
    except KeyboardInterrupt:
        print("\n\nKeyboardInterrupt received\n\n", flush=True)
    except SystemExit as e:
        print(f"\n\nSystemExit with code {e.code}\n\n", flush=True)
    except Exception as e:
        print(f"\n\nUnhandled exception: {e}\n\n", flush=True)
        import traceback
        traceback.print_exc()
