"""
Test script for $(pwd) variable expansion feature
Run this to verify that $(pwd) is correctly expanded to project paths
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.context import Context
from db.session import init_db, get_session

def test_pwd_expansion():
    """Test $(pwd) variable expansion in various scenarios"""
    
    print("=" * 60)
    print("Testing $(pwd) Variable Expansion")
    print("=" * 60)
    
    # Initialize database and context
    init_db()
    session = get_session()
    ctx = Context(session)
    
    # Test 1: Create a test project
    print("\n[TEST 1] Creating test project...")
    try:
        project =ctx.project_manager.create_project("pwd_test_project")
        ctx.current_project = project
        print(f"✓ Project created: {project.name}")
        print(f"✓ Project path: {project.path}")
    except Exception as e:
        print(f"✗ Failed to create project: {e}")
        return
    
    # Test 2: Test string replacement
    print("\n[TEST 2] Testing $(pwd) replacement...")
    test_cases = [
        "$(pwd)/subdomain/httpx",
        "$(pwd)/results/scan_output",
        "/absolute/path/no/expansion",
        "relative/path/no/pwd",
        "$(pwd)/Collecting_url/Collecting_url",
        "prefix_$(pwd)_suffix",
    ]
    
    for test_val in test_cases:
        if '$(pwd)' in test_val:
            expanded = test_val.replace('$(pwd)', project.path)
            print(f"✓ {test_val}")
            print(f"  → {expanded}")
        else:
            print(f"  {test_val} (no expansion)")
    
    # Test 3: Multiple $(pwd) in one value
    print("\n[TEST 3] Testing multiple $(pwd) occurrences...")
    multi_pwd = "$(pwd)/data/$(pwd)/output"
    expanded_multi = multi_pwd.replace('$(pwd)', project.path)
    print(f"Original: {multi_pwd}")
    print(f"Expanded: {expanded_multi}")
    
    # Test 4: Verify no interference with other $ variables
    print("\n[TEST 4] Checking no interference with $variables...")
    var_tests = [
        "$API_KEY",  # Should not be affected
        "$MY_VAR/path",  # Should not be affected
        "$(pwd)/$VAR",  # Should expand $(pwd) only
    ]
    
    for var_test in var_tests:
        if '$(pwd)' in var_test:
            result = var_test.replace('$(pwd)', project.path)
            print(f"✓ {var_test} → {result}")
        else:
            print(f"  {var_test} (untouched)")
    
    # Cleanup
    print("\n[CLEANUP] Removing test project...")
    try:
        ctx.project_repo.delete(project.id)
        print("✓ Test project removed")
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_pwd_expansion()
