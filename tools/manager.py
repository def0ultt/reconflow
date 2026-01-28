from core.base import BaseModule
from core.yaml_module import GenericYamlModule
from core.workflow_module import WorkflowModule
import os
import glob
import re

class ToolManager:
    """
    Registry for ReconFlow modules.
    """
    def __init__(self):
        self.modules = {}

    def register_module(self, path: str, module_class):
        """Register a module class with a path (e.g., 'scan/subdomain/passive')."""
        self.modules[path] = module_class

    def load_yaml_modules(self, root_dir="modules"):
        """Scans for .yml files in modules/ directory and registers them."""
        # Recursive glob
        patterns = [
            os.path.join(root_dir, "**", "*.yml"),
            os.path.join(root_dir, "**", "*.yaml")
        ]
        
        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                # Determine virtual path from file structure
                # e.g. modules/recon/passive/subdomain.yml -> recon/passive/subdomain
                
                rel_path = os.path.relpath(filepath, root_dir)
                base, _ = os.path.splitext(rel_path)
                
                # Normalize path separators
                module_path = base.replace(os.path.sep, "/")
                
                # Create a flexible factory/class for this specifics YAML
                # We need a unique class or instance factory. 
                # Registering the GenericYamlModule class directly wouldn't work because it needs the file path.
                
                # Solution: Create a closure/factory or use a lambda that returns the configured instance?
                # But our get_module() expects a CLASS that it instantiates.
                # Create Dynamic Class (GenericYamlModule) specific to this file
                # Use default arg to bind closure
                class DynamicYamlModule(GenericYamlModule):
                    def __init__(self_inner, path=filepath):
                         super().__init__(yaml_path=path)
                
                # Check validation (Schema)
                try:
                     temp = GenericYamlModule(filepath)
                     DynamicYamlModule.meta = temp.meta
                except Exception as e:
                     print(f"Failed to load YAML module {filepath}: {e}")
                     continue

                self.modules[module_path] = DynamicYamlModule
                print(f"[+] Registered YAML module: {module_path}")

    def load_workflow_modules(self, root_dir="workflows"):
        """
        Scans for .yml workflows and registers them as modules under 'workflow/xxx'.
        This allows 'use workflow/my_flow'.
        """
        patterns = [
            os.path.join(root_dir, "**", "*.yml"),
            os.path.join(root_dir, "**", "*.yaml")
        ]
        
        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                # virtual path: workflows/custom/my_flow.yml -> workflow/custom/my_flow
                rel_path = os.path.relpath(filepath, root_dir)
                base, _ = os.path.splitext(rel_path)
                
                # Prefix with 'workflow/'
                module_path = "workflow/" + base.replace(os.path.sep, "/")
                
                if module_path in self.modules:
                    continue # Already registered?

                # Create Dynamic WorkflowModule
                class DynamicWorkflowModule(WorkflowModule):
                    def __init__(self_inner, path=filepath):
                         super().__init__(yaml_path=path)
                         
                try:
                     temp = WorkflowModule(filepath)
                     DynamicWorkflowModule.meta = temp.meta
                except Exception as e:
                     print(f"Failed to load Workflow module {filepath}: {e}")
                     continue

                self.modules[module_path] = DynamicWorkflowModule
                print(f"[+] Registered Workflow module: {module_path}")

    def get_module(self, path: str):
        module_cls = self.modules.get(path)
        if module_cls:
            return module_cls() # Return a new instance
        return None

    def list_modules(self):
        return sorted(list(self.modules.keys()))

    def list_pure_modules(self):
        """Returns only standard modules (not workflows)."""
        return sorted([k for k in self.modules.keys() if not k.startswith("workflow/")])

    def list_workflow_modules(self):
        """Returns only workflow modules."""
        return sorted([k for k in self.modules.keys() if k.startswith("workflow/")])

    def get_module_by_id(self, idx: int):
        modules = self.list_modules()
        if 0 <= idx < len(modules):
            return modules[idx] # Return path
        return None

    def search_modules(self, pattern: str):
        """Search modules by path or description using regex."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            print(f" Invalid regex: {pattern}")
            return []

        results = []
        modules = self.list_modules()
        
        for i, path in enumerate(modules):
            module_cls = self.modules[path]
            # Instantiate to get meta info
            try:
                mod = module_cls()
                name = mod.meta.get('name', '')
                desc = mod.meta.get('description', '')
                
                if regex.search(path) or regex.search(name) or regex.search(desc):
                    results.append((i, path, mod.meta))
            except Exception:
                pass
                
        return results
