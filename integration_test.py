from core.context import Context
from core.yaml_module import GenericYamlModule
import sys

def main():
    print("--- Starting Integration Test ---")
    ctx = Context()
    
    # Manually load the module (simulating 'use' command or file loading)
    mod_path = "examples/demo_unified.yml"
    print(f"Loading {mod_path}...")
    
    try:
        mod = GenericYamlModule(mod_path)
    except Exception as e:
        print(f"Failed to load module: {e}")
        sys.exit(1)
        
    print("Running module options check...")
    # Simulate user input for vars? No, using defaults.
    # Check if defaults populated.
    if mod.options['target'].value != 'localhost':
        print(f"FAIL: Default value for target incorrect. Got {mod.options['target'].value}")
        sys.exit(1)
        
    print("Executing run()...")
    try:
        results = mod.run(ctx)
        
        # Verify output
        print("Results:", results)
        
        if 'step1' in results and 'step4_end' in results:
             print("✅ Integration Test PASSED")
        else:
             print("❌ Integration Test FAILED (Missing results)")
             sys.exit(1)
             
    except Exception as e:
        print(f"❌ Execution Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
