import sys
from io import StringIO
from rich.console import Console

# Mock dependencies
class MockContext:
    def __init__(self):
        self.current_project = None
        self.tool_manager = None

# Mock Module extending the modified classes
from core.yaml_module import GenericYamlModule
from core.schema import ModuleSchema, ModuleInfo, Step

class TestOutput(GenericYamlModule):
    def __init__(self):
        super().__init__()
        # Manually construct a simple schema
        self.schema = ModuleSchema(
            type="module",
            info=ModuleInfo(id="test", name="Test", author="me"),
            vars={},
            steps=[
                Step(name="echo", tool="echo", args="'hello'")
            ]
        )

# Redirect visible output
capture = StringIO()
console = Console(file=capture)
# Monkey patch the console used in formatting
import utils.output_formatter
utils.output_formatter.console = console

print("Running in FOREGROUND (should see output)...")
mod = TestOutput()
try:
    mod.run(MockContext(), background=False)
except Exception as e:
    print(f"Foreground run failed: {e}")

foreground_output = capture.getvalue()
print(f"Captured Foreground Output Length: {len(foreground_output)}")
if "Running" not in foreground_output:
    print("WARNING: Did not see expected output in foreground run.")

# Reset capture
capture.truncate(0)
capture.seek(0)

print("\nRunning in BACKGROUND (should be silent)...")
try:
    mod.run(MockContext(), background=True)
except Exception as e:
    print(f"Background run failed: {e}")

background_output = capture.getvalue()
print(f"Captured Background Output Length: {len(background_output)}")

if len(background_output) == 0:
    print("[SUCCESS] Background run produced NO output!")
else:
    print("[FAILURE] Background run produced output:")
    print(background_output)
