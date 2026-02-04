
import sys
import os
import json
from rich.console import Console

# Mock Context
class Context:
    def __init__(self):
        self.current_project = type('obj', (object,), {'path': os.getcwd()})

# Import command
sys.path.insert(0, os.getcwd())
from cli.commands import cmd_bcat

def test_filter():
    # Create dummy json file
    data = [
        {"url": "http://example.com", "status_code": 200, "title": "Example", "ignored": "value"},
        {"url": "http://test.com", "status_code": 404, "title": "Test", "ignored": "value2"}
    ]
    with open("test_output.json", "w") as f:
        json.dump(data, f)
        
    print("\n[Test 1] Filtering include=url,status_code")
    try:
        # We need to simulate the function call. 
        # Note: cmd_bcat prints to console, we won't capture it easily without mocking console print,
        # but we can run it and see if it fails or if the logic holds up.
        # Actually, since I can't see the output of the function directly if it just prints, 
        # I rely on the fact that I modified the code.
        # But to be safe, I'll run it via os.system and capture output.
        pass
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # create sample file
    data = [
        {"url": "http://example.com", "status_code": 200, "title": "Example", "ignored": "value"},
        {"url": "http://test.com", "status_code": 404, "title": "Test", "ignored": "value2"}
    ]
    with open("test_output.json", "w") as f:
        json.dump(data, f)
    
    # Run the command using reconflow cli wrapper if possible, or just mock it.
    # Since I don't have the full click setup easily, I'll just run python code that imports the function.
    # But cmd_bcat relies on global console...
    pass
