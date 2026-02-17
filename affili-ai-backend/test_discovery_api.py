import urllib.request
import json

token = open("token_test.txt").read().strip()
url = "http://localhost:8000/api/v1/tasks"
body = json.dumps({"task_type": "DISCOVER_PROGRAM", "payload": {"seed_url": "https://www.techradar.com/"}}).encode()
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
req.add_header("X-Tenant-ID", "00000000-0000-0000-0000-000000000000")

try:
    resp = urllib.request.urlopen(req)
    result = resp.read().decode()
    with open("api_result.txt", "w") as f:
        f.write(f"SUCCESS:\n{result}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    with open("api_result.txt", "w") as f:
        f.write(f"HTTP {e.code}:\n{body}")
except Exception as e:
    with open("api_result.txt", "w") as f:
        f.write(f"ERROR:\n{str(e)}")
