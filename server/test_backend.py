import requests
import asyncio
import websockets
import json
import threading
import time

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws/logs"

# Dummy Workflow
WORKFLOW = {
    "type": "module",
    "info": {
        "id": "test-workflow",
        "name": "Test",
        "author": "Tester"
    },
    "vars": {
        "target": {"type": "string", "default": "example.com"}
    },
    "steps": [
        {
            "name": "echo_test",
            "tool": "echo",
            "args": "Hello {{target}}"
        }
    ]
}

async def listen_logs(execution_id):
    uri = f"{WS_URL}/{execution_id}"
    print(f"Connecting to WS: {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket. Waiting for logs...")
            while True:
                msg = await websocket.recv()
                print(f"[WS Log] {msg}")
    except Exception as e:
        print(f"WS Error/Closed: {e}")

def test_projects():
    print("\n--- Testing Projects API ---")
    # 1. List
    res = requests.get(f"{API_URL}/api/projects")
    print(f"List Projects: {res.status_code}")
    
    # 2. Create Temp
    print("Creating Temp Project...")
    res = requests.post(f"{API_URL}/api/projects", json={"name": "test-temp", "is_temp": True})
    if res.status_code == 200:
        proj = res.json()
        print(f"Created: {proj['name']} (ID: {proj['id']}) Path: {proj['path']}")
        
        # 3. Get Details
        res = requests.get(f"{API_URL}/api/projects/{proj['id']}")
        print(f"Get Details: {res.status_code}")
        
        # 4. Delete
        res = requests.delete(f"{API_URL}/api/projects/{proj['id']}")
        print(f"Delete: {res.status_code}")
    else:
        print(f"Create Failed: {res.text}")

def run_test():
    test_projects()
    
    # 1. Trigger Run
    print("\n--- Testing Workflow API ---")
    print("Triggering Workflow...")
    try:
        res = requests.post(f"{API_URL}/api/run", json={"workflow": WORKFLOW, "variables": {"target": "World"}})
        if res.status_code != 200:
            print(f"Failed to start: {res.text}")
            return
        
        data = res.json()
        exec_id = data['execution_id']
        print(f"Execution ID: {exec_id}")
        
        # 2. Listen to logs (needs to run concurrently)
        # We can't easily sync listen here because run is async check.
        # But server is running, so we can connect.
        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(listen_logs(exec_id))
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    print("Make sure server is running: python3 server/main.py")
    time.sleep(1)
    run_test()
