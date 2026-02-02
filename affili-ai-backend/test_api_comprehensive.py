#!/usr/bin/env python
"""Comprehensive API tests"""
import requests
import json

base_url = "http://127.0.0.1:8000/api/v1"

print("=" * 60)
print("TESTING AFFILI-AI BACKEND API")
print("=" * 60)

# Test 1: List programs
print("\n1. GET /programs (should be empty)")
try:
    r = requests.get(f"{base_url}/programs")
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Programs found: {len(data)}")
    if r.status_code == 200:
        print("   ✓ PASSED\n")
    else:
        print(f"   ✗ FAILED\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")
    import traceback
    traceback.print_exc()

# Test 2: Create program
print("2. POST /programs (create new program)")
program_id = None
try:
    program_data = {
        "name": "Amazon Associates",
        "affiliate_url": "https://amazon.com/join/affiliate",
        "commission_rate": 5.5,
        "description": "Amazon's affiliate program"
    }
    r = requests.post(f"{base_url}/programs", json=program_data)
    print(f"   Status: {r.status_code}")
    if r.status_code == 201:
        program = r.json()
        program_id = program['id']
        print(f"   Created: {program['name']} (ID: {str(program_id)[:8]}...)")
        print("   ✓ PASSED\n")
    else:
        print(f"   ✗ FAILED: {r.text}\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")
    import traceback
    traceback.print_exc()

# Test 3: Get program
if program_id:
    print(f"3. GET /programs/{{id}}")
    try:
        r = requests.get(f"{base_url}/programs/{program_id}")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✓ PASSED\n")
        else:
            print(f"   ✗ FAILED\n")
    except Exception as e:
        print(f"   ✗ ERROR: {e}\n")

# Test 4: List again
print("4. GET /programs (should have 1+ programs)")
try:
    r = requests.get(f"{base_url}/programs")
    programs = r.json()
    print(f"   Status: {r.status_code}")
    print(f"   Found: {len(programs)} program(s)")
    if len(programs) > 0:
        print("   ✓ PASSED\n")
    else:
        print("   ✗ FAILED\n")
except Exception as e:
    print(f"   ✗ ERROR: {e}\n")

print("=" * 60)
print("API TESTS COMPLETE")
print("=" * 60)
