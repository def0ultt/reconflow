
import sys
import os
import json
from unittest.mock import MagicMock
from rich.console import Console

sys.path.append(os.path.abspath('reconflow'))

from cli.commands import cmd_bcat
from core.context import Context
from io import StringIO

# Setup Console capture
capture_buf = StringIO()
console = Console(file=capture_buf)
from cli import commands
commands.console = console

def setup_test_files():
    os.makedirs('results/projects/test/format-test', exist_ok=True)
    
    # JSON Array format
    json_array = [
        {"url": "https://json-array.com", "status_code": 200},
        {"url": "https://json-array2.com", "status_code": 404}
    ]
    with open('results/projects/test/format-test/data.json', 'w') as f:
        json.dump(json_array, f)
    
    # JSONL format
    with open('results/projects/test/format-test/data.jsonl', 'w') as f:
        f.write('{"url": "https://jsonl1.com", "status_code": 200}\n')
        f.write('{"url": "https://jsonl2.com", "status_code": 404}\n')

def test_formats():
    ctx = MagicMock(spec=Context)
    ctx.current_project = MagicMock()
    ctx.current_project.path = os.path.abspath('results/projects/test')

    # Test JSON array
    print("\n--- Test 1: JSON Array Format ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "format-test/data.json")
    output = capture_buf.getvalue()
    if "https://json-array.com" in output and "Showing all 2 records" in output:
        print("✓ PASS")
    else:
        print(f"✗ FAIL:\n{output}")

    # Test JSONL
    print("\n--- Test 2: JSONL Format ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "format-test/data.jsonl")
    output = capture_buf.getvalue()
    if "https://jsonl1.com" in output and "Showing all 2 records" in output:
        print("✓ PASS")
    else:
        print(f"✗ FAIL:\n{output}")

    # Test search on JSON array
    print("\n--- Test 3: Search on JSON Array ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "status_code==200 format-test/data.json")
    output = capture_buf.getvalue()
    if "https://json-array.com" in output and "(1 records)" in output:
        print("✓ PASS")
    else:
        print(f"✗ FAIL:\n{output}")

if __name__ == "__main__":
    setup_test_files()
    test_formats()
