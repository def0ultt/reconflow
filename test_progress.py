"""
Test script to verify progress indicator functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.yaml_module import GenericYamlModule
from core.context import Context
from db.database import Database
from tools.manager import ToolManager
from db.repositories import ProjectRepository
from config.settings import SettingsManager
from cli.session_manager import SessionManager

# Create test context
db = Database()
tool_manager = ToolManager()
project_repo = ProjectRepository(db)
settings_manager = SettingsManager(db)
session_manager = SessionManager(db)

ctx = Context(
    db=db,
    tool_manager=tool_manager,
    project_repo=project_repo,
    settings_manager=settings_manager,
    session_manager=session_manager
)

# Load a test module
print("Loading test module...")
module_path = "modules/test/boolean_test.yml"

if os.path.exists(module_path):
    module = GenericYamlModule(module_path)
    
    # Set required options
    print("\nSetting module options...")
    for name, opt in module.options.items():
        if opt.required and opt.value is None:
            # Set test values
            if name == "target":
                module.update_option(name, "example.com")
            elif name == "verbose":
                module.update_option(name, True)
            elif name == "output":
                module.update_option(name, "/tmp/test_output.txt")
    
    print("\nStarting module execution with progress tracking...\n")
    
    # Run the module (this should show progress)
    try:
        results = module.run(ctx)
        print("\n\nExecution completed!")
        print(f"Results: {len(results)} steps executed")
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Module not found: {module_path}")
    print("\nAvailable test modules:")
    test_dir = "modules/test"
    if os.path.exists(test_dir):
        for f in os.listdir(test_dir):
            if f.endswith('.yml'):
                print(f"  - {os.path.join(test_dir, f)}")
