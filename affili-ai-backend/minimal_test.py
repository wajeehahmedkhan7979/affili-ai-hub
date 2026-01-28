"""Minimal FastAPI test"""
from fastapi import FastAPI
import sys

print("stdout test - app loading", file=sys.stdout, flush=True)
print("stderr test - app loading", file=sys.stderr, flush=True)

app = FastAPI()

@app.get("/test")
def test():
    print("DEBUG: test() called", flush=True)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal server...", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    uvicorn.run(app, host="127.0.0.1", port=9000)
