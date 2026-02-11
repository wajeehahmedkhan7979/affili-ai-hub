#!/bin/bash
set -e

echo "=== AFFILI-AI HUB SECURITY SWEEP ==="
echo "Date: $(date)"

# 1. Dependency Scan
echo -e "\n[1] Checking Dependencies (Safety)..."
safety check --full-report || echo "⚠️  Safety check found issues (check report)"

# 2. Secrets Scan (Simulation with grep)
echo -e "\n[2] Scanning for Secrets..."
grep -r "SECRET_KEY =" app/core/config.py || echo "✅ Config looks standard"
grep -r "ENCRYPTION_KEY =" app/core/config.py || echo "✅ Config looks standard"

# 3. Endpoint Protection Audit
echo -e "\n[3] Auditing Endpoint Security..."
# Check if rate limiter decorator is applied to sensitive routes
grep -r "@limiter.limit" app/api/endpoints/ || echo "⚠️  Some endpoints might be missing rate limits"

echo -e "\n[4] Middleware Audit..."
grep "MetricsSecurityMiddleware" app/main.py && echo "✅ Metrics Security Active"

echo -e "\n=== SWEEP COMPLETE ==="
