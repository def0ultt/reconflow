
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
    os.makedirs('results/projects/test/field-test', exist_ok=True)
    
    # Create test JSON file
    data = [
        {"url": "https://example.com", "status_code": 200, "title": "Example", "timestamp": "2026-01-01", "hash": "abc123"},
        {"url": "https://test.com", "status_code": 404, "title": "Not Found", "timestamp": "2026-01-02", "hash": "def456"}
    ]
    
    with open('results/projects/test/field-test/data.json', 'w') as f:
        json.dump(data, f)

def test_field_filtering():
    ctx = MagicMock(spec=Context)
    ctx.current_project = MagicMock()
    ctx.current_project.path = os.path.abspath('results/projects/test')

    # Test 1: Include only specific fields
    print("\n--- Test 1: --include=url,status_code ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "field-test/data.json --include=url,status_code")
    output = capture_buf.getvalue()
    if "url: https://example.com" in output and "status_code: 200" in output:
        if "title:" not in output and "timestamp:" not in output:
            print("✓ PASS - Only included fields displayed")
        else:
            print("✗ FAIL - Excluded fields were shown")
    else:
        print(f"✗ FAIL:\n{output}")

    # Test 2: Exclude specific fields
    print("\n--- Test 2: --exclude=timestamp,hash ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "field-test/data.json --exclude=timestamp,hash")
    output = capture_buf.getvalue()
    if "url: https://example.com" in output and "title: Example" in output:
        if "timestamp:" not in output and "hash:" not in output:
            print("✓ PASS - Excluded fields hidden")
        else:
            print("✗ FAIL - Excluded fields were shown")
    else:
        print(f"✗ FAIL:\n{output}")

    # Test 3: Mutual exclusivity error
    print("\n--- Test 3: --include + --exclude (should error) ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "field-test/data.json --include=url --exclude=hash")
    output = capture_buf.getvalue()
    if "Cannot use --include and --exclude together" in output:
        print("✓ PASS - Mutual exclusivity enforced")
    else:
        print(f"✗ FAIL:\n{output}")

    # Test 4: Include with search query
    print("\n--- Test 4: 'status_code==200' --include=url,title ---")
    capture_buf.truncate(0)
    capture_buf.seek(0)
    cmd_bcat(ctx, "'status_code==200' field-test/data.json --include=url,title")
    output = capture_buf.getvalue()
    if "url: https://example.com" in output and "title: Example" in output:
        if "(1 records)" in output and "status_code:" not in output:
            print("✓ PASS - Search + include works")
        else:
            print("✗ FAIL - Search or filtering incorrect")
    else:
        print(f"✗ FAIL:\n{output}")

if __name__ == "__main__":
    setup_test_files()
    test_field_filtering()
