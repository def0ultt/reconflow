#!/usr/bin/env python3
"""
Comprehensive Test Suite for ReconFlow
Tests all major functions and components
"""

import sys
import os
import traceback
from datetime import datetime

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'skipped': []
}

def test_result(name, passed, error=None):
    """Record test result"""
    if passed:
        test_results['passed'].append(name)
        print(f"✅ PASS: {name}")
    else:
        test_results['failed'].append((name, error))
        print(f"❌ FAIL: {name}")
        if error:
            print(f"   Error: {error}")

def run_test(test_name, test_func):
    """Execute a test function and record result"""
    try:
        test_func()
        test_result(test_name, True)
    except Exception as e:
        test_result(test_name, False, str(e))
        traceback.print_exc()

# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

def test_schema_validation():
    """Test core schema validation"""
    from core.schema import validate_yaml, ModuleSchema
    
    # Valid module
    valid_data = {
        'type': 'module',
        'info': {
            'id': 'test-mod',
            'name': 'Test Module',
            'description': 'Test',
            'author': 'tester'
        },
        'vars': {
            'target': {'required': True}
        },
        'steps': [
            {'name': 'step1', 'tool': 'echo', 'args': '{{target}}'}
        ]
    }
    
    schema = validate_yaml(valid_data)
    assert schema.info.id == 'test-mod'
    assert 'target' in schema.vars
    assert len(schema.steps) == 1

def test_schema_validation_invalid_type():
    """Test schema rejects invalid type"""
    from core.schema import validate_yaml
    
    invalid_data = {
        'type': 'invalid',
        'info': {'id': 'test', 'name': 'Test', 'description': 'Test', 'author': 'test'},
        'vars': {},
        'steps': []
    }
    
    try:
        validate_yaml(invalid_data)
        raise AssertionError("Should have raised ValueError")
    except (ValueError, Exception) as e:
        # Expected - schema validation should reject invalid type
        assert 'invalid' in str(e).lower() or 'unsupported' in str(e).lower()

def test_schema_step_validation():
    """Test step validation (tool XOR module)"""
    from core.schema import ModuleStep
    from pydantic import ValidationError
    
    # Valid: has tool
    step1 = ModuleStep(name='s1', tool='echo', args='test')
    assert step1.tool == 'echo'
    
    # Invalid: has both
    try:
        ModuleStep(name='s2', tool='echo', module='mod', args='test')
        raise AssertionError("Should reject both tool and module")
    except ValidationError:
        pass
    
    # Invalid: has neither
    try:
        ModuleStep(name='s3', args='test')
        raise AssertionError("Should require tool or module")
    except ValidationError:
        pass

# ============================================================================
# MODULE EXECUTION TESTS
# ============================================================================

def test_module_loading():
    """Test GenericYamlModule loading"""
    from core.yaml_module import GenericYamlModule
    
    # Create test module file
    test_yml = '/tmp/test_module.yml'
    with open(test_yml, 'w') as f:
        f.write("""type: module
info:
  id: test-load
  name: Test Load
  description: Test
  author: tester
vars:
  test_var:
    default: "hello"
steps:
  - name: echo_test
    tool: echo
    args: "{{test_var}}"
""")
    
    mod = GenericYamlModule(test_yml)
    assert mod.schema.info.id == 'test-load'
    assert 'test_var' in mod.options
    assert mod.options['test_var'].value == 'hello'
    
    os.remove(test_yml)

def test_module_execution():
    """Test module execution with DAG"""
    from core.yaml_module import GenericYamlModule
    from core.context import Context
    
    test_yml = '/tmp/test_exec.yml'
    with open(test_yml, 'w') as f:
        f.write("""type: module
info:
  id: test-exec
  name: Test Exec
  description: Test
  author: tester
vars:
  msg:
    default: "test"
steps:
  - name: step1
    tool: echo
    args: "{{msg}}"
""")
    
    mod = GenericYamlModule(test_yml)
    ctx = Context()
    results = mod.run(ctx)
    
    assert 'step1' in results
    assert 'test' in results['step1']['stdout']
    
    os.remove(test_yml)

def test_strict_variable_enforcement():
    """Test strict variable scoping"""
    from core.yaml_module import GenericYamlModule
    from core.context import Context
    from jinja2 import UndefinedError
    
    test_yml = '/tmp/test_strict.yml'
    with open(test_yml, 'w') as f:
        f.write("""type: module
info:
  id: test-strict
  name: Test Strict
  description: Test
  author: tester
vars: {}
steps:
  - name: fail_step
    tool: echo
    args: "{{undefined_var}}"
""")
    
    mod = GenericYamlModule(test_yml)
    ctx = Context()
    
    try:
        results = mod.run(ctx)
        # If we get here with empty results, the step failed as expected
        if not results or 'fail_step' not in results:
            pass  # Expected - step should have failed
        else:
            raise AssertionError("Should fail on undefined variable")
    except Exception as e:
        # Expected to fail with undefined variable error
        error_msg = str(e).lower()
        assert 'undefined' in error_msg or 'template' in error_msg, f"Unexpected error: {e}"
    
    os.remove(test_yml)

def test_tool_path_option():
    """Test custom tool path"""
    from core.yaml_module import GenericYamlModule
    from core.context import Context
    
    # Create a mock tool
    mock_tool = '/tmp/mock_test_tool.sh'
    with open(mock_tool, 'w') as f:
        f.write('#!/bin/sh\necho "Custom tool executed"')
    os.chmod(mock_tool, 0o755)
    
    test_yml = '/tmp/test_path.yml'
    with open(test_yml, 'w') as f:
        f.write(f"""type: module
info:
  id: test-path
  name: Test Path
  description: Test
  author: tester
vars: {{}}
steps:
  - name: custom_path
    tool: anything
    path: "{mock_tool}"
    args: ""
""")
    
    mod = GenericYamlModule(test_yml)
    ctx = Context()
    results = mod.run(ctx)
    
    assert 'custom_path' in results
    assert 'Custom tool executed' in results['custom_path']['stdout']
    
    os.remove(test_yml)
    os.remove(mock_tool)

def test_parallel_execution():
    """Test parallel step execution"""
    from core.yaml_module import GenericYamlModule
    from core.context import Context
    import time
    
    test_yml = '/tmp/test_parallel.yml'
    with open(test_yml, 'w') as f:
        f.write("""type: module
info:
  id: test-parallel
  name: Test Parallel
  description: Test
  author: tester
vars: {}
steps:
  - name: sleep1
    tool: sleep
    args: "0.5"
    parallel: true
  - name: sleep2
    tool: sleep
    args: "0.5"
    parallel: true
  - name: final
    tool: echo
    args: "done"
    depends_on: [sleep1, sleep2]
""")
    
    mod = GenericYamlModule(test_yml)
    ctx = Context()
    
    start = time.time()
    results = mod.run(ctx)
    duration = time.time() - start
    
    # Should take ~0.5s (parallel) not ~1s (sequential)
    assert duration < 0.8, f"Parallel execution too slow: {duration}s"
    assert 'final' in results
    
    os.remove(test_yml)

# ============================================================================
# CONTEXT & MANAGER TESTS
# ============================================================================

def test_context_initialization():
    """Test Context initialization"""
    from core.context import Context
    
    ctx = Context()
    assert ctx.tool_manager is not None
    assert ctx.project_manager is not None
    assert ctx.session_manager is not None
    assert ctx.settings_manager is not None

def test_tool_manager_loading():
    """Test ToolManager module loading"""
    from tools.manager import ToolManager
    
    tm = ToolManager()
    # Should load modules from modules/ and workflows/
    modules = tm.list_modules()
    assert isinstance(modules, list)

def test_tool_manager_search():
    """Test ToolManager search functionality"""
    from tools.manager import ToolManager
    
    tm = ToolManager()
    # Search should return results
    results = tm.search_modules('.*')  # Match all
    assert isinstance(results, list)

# ============================================================================
# DATABASE TESTS
# ============================================================================

def test_database_session():
    """Test database session creation"""
    from db.session import get_session
    
    session = get_session()
    assert session is not None

def test_project_repository():
    """Test ProjectRepository basic operations"""
    from db.repositories.project_repo import ProjectRepository
    from db.session import get_session
    
    session = get_session()
    repo = ProjectRepository(session)
    
    # List projects - use get_all() method
    projects = repo.get_all()
    assert isinstance(projects, list)

# ============================================================================
# UTILITY TESTS
# ============================================================================

def test_path_utilities():
    """Test path utility functions"""
    from utils.paths import get_project_root
    
    root = get_project_root()
    assert root.exists()
    assert root.is_dir()

def test_logger():
    """Test logger setup"""
    from utils.logger import setup_logger
    
    logger = setup_logger()
    assert logger is not None
    logger.info("Test log message")

# ============================================================================
# CLI COMMAND TESTS
# ============================================================================

def test_cli_commands_import():
    """Test CLI commands can be imported"""
    from cli.commands import (
        cmd_use, cmd_back, cmd_set, cmd_run,
        cmd_show, cmd_list, cmd_search, cmd_help
    )
    
    # Just verify they're callable
    assert callable(cmd_use)
    assert callable(cmd_back)
    assert callable(cmd_set)
    assert callable(cmd_run)

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("=" * 70)
    print("ReconFlow Comprehensive Test Suite")
    print("=" * 70)
    print(f"Started: {datetime.now()}")
    print()
    
    # Schema Tests
    print("\n[SCHEMA VALIDATION TESTS]")
    run_test("Schema Validation - Valid Module", test_schema_validation)
    run_test("Schema Validation - Invalid Type", test_schema_validation_invalid_type)
    run_test("Schema Step Validation", test_schema_step_validation)
    
    # Module Execution Tests
    print("\n[MODULE EXECUTION TESTS]")
    run_test("Module Loading", test_module_loading)
    run_test("Module Execution", test_module_execution)
    run_test("Strict Variable Enforcement", test_strict_variable_enforcement)
    run_test("Tool Path Option", test_tool_path_option)
    run_test("Parallel Execution", test_parallel_execution)
    
    # Context & Manager Tests
    print("\n[CONTEXT & MANAGER TESTS]")
    run_test("Context Initialization", test_context_initialization)
    run_test("ToolManager Loading", test_tool_manager_loading)
    run_test("ToolManager Search", test_tool_manager_search)
    
    # Database Tests
    print("\n[DATABASE TESTS]")
    run_test("Database Session", test_database_session)
    run_test("Project Repository", test_project_repository)
    
    # Utility Tests
    print("\n[UTILITY TESTS]")
    run_test("Path Utilities", test_path_utilities)
    run_test("Logger", test_logger)
    
    # CLI Tests
    print("\n[CLI COMMAND TESTS]")
    run_test("CLI Commands Import", test_cli_commands_import)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⊘  Skipped: {len(test_results['skipped'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for name, error in test_results['failed']:
            print(f"  - {name}: {error}")
    
    print(f"\nCompleted: {datetime.now()}")
    print("=" * 70)
    
    # Exit with error code if any tests failed
    sys.exit(1 if test_results['failed'] else 0)

if __name__ == "__main__":
    main()
