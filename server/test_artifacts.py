import requests
import json
import os
import time

BASE_URL = "http://localhost:8000/api"

def wait_for_server():
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/projects/")
            return True
        except:
            time.sleep(1)
    return False

if not wait_for_server():
    print("Server failed to start")
    exit(1)

# 1. Create Project
print("[*] Creating Project...")
res = requests.post(f"{BASE_URL}/projects/", json={"name": "artifact-test", "is_temp": True})
if res.status_code != 200:
    print(f"Failed to create project: {res.text}")
    exit(1)
    
proj = res.json()
pid = proj['id']
path = proj['path']
print(f"[+] Project created: ID={pid}, Path={path}")

# 2. Create Dummy Artifact using FS
print("[*] Creating dummy artifact...")
os.makedirs(path, exist_ok=True)
dummy_data = {"host": "example.com", "ports": [80, 443]}
with open(os.path.join(path, "results.json"), "w") as f:
    json.dump(dummy_data, f)
    
# 3. List Artifacts
print("[*] Listing artifacts...")
res = requests.get(f"{BASE_URL}/projects/{pid}/artifacts")
if res.status_code != 200:
    print(f"Failed to list artifacts: {res.text}")
    exit(1)

artifacts = res.json()
print(f"[+] Artifacts: {json.dumps(artifacts, indent=2)}")

expected_file = next((f for f in artifacts if f['name'] == 'results.json'), None)
if not expected_file:
    print("[-] Error: results.json not found in list")
    exit(1)

# 4. Get Content
print("[*] Getting content...")
res = requests.get(f"{BASE_URL}/projects/{pid}/artifacts/results.json")
if res.status_code != 200:
    print(f"Failed to get content: {res.text}")
    exit(1)
    
content = res.json()
print(f"[+] Content: {content}")

if content['content']['host'] == 'example.com':
    print("[+] SUCCESS: Content matches")
else:
    print("[-] FAILURE: Content mismatch")
