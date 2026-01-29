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
        self.aliases = {} # Maps legacy paths or custom aliases to full names

    def _generate_full_name(self, tool_type: str, tool_id: str) -> str:
        """
        Generates the full name for a tool based on its type and ID.
        Format: /{type}/{id}
        """
        return f"/{tool_type}/{tool_id}"

    def register_tool(self, tool_type: str, tool_id: str, module_class, aliases: list = None):
        """
        Registers a tool (module or workflow) with a unique ID.
        Enforces naming convention and checks for duplicates.
        Can optionally register aliases (pointers to the full name).
        """
        full_name = self._generate_full_name(tool_type, tool_id)
        
        if full_name in self.modules:
            print(f"[-]Error: {tool_type} with id '{tool_id}' already exists.")
            return

        self.modules[full_name] = module_class
        print(f"[+] Registered {tool_type}: {full_name}")
        
        # Register Aliases
        if aliases:
            for alias in aliases:
                # Avoid overwriting modules with aliases if collision? 
                # Prioritize explicit registration.
                if alias not in self.modules and alias not in self.aliases:
                    self.aliases[alias] = full_name
                    # print(f"    (Alias: {alias})")

    def load_yaml_modules(self, root_dir="modules"):
        """Scans for .yml files in modules/ directory and registers them."""
        # Recursive glob
        patterns = [
            os.path.join(root_dir, "**", "*.yml"),
            os.path.join(root_dir, "**", "*.yaml")
        ]
        
        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                # Calculate legacy path for alias
                rel_path = os.path.relpath(filepath, root_dir)
                base, _ = os.path.splitext(rel_path)
                legacy_path = base.replace(os.path.sep, "/")
                
                # Check validation (Schema) & Get Metadata
                try:
                     temp = GenericYamlModule(filepath)
                     mod_meta = temp.meta.copy()
                     tool_id = mod_meta.get('id')
                     
                     if not tool_id:
                         print(f"Skipping {filepath}: Missing metadata.id")
                         continue

                     # Create a unique Dynamic Class for this specific YAML
                     # We use type() to create a new class type dynamically
                     # This ensures class attributes like 'meta' don't collide.
                     
                     # Closure to capture 'filepath'
                     def make_init(path):
                        def __init__(self_inner):
                             super(GenericYamlModule, self_inner).__init__()
                             GenericYamlModule.__init__(self_inner, yaml_path=path)
                        return __init__

                     # Unique class name
                     safe_name = "DynamicMod_" + "".join(x for x in tool_id if x.isalnum())
                     
                     # Create class
                     DynamicModuleClass = type(safe_name, (GenericYamlModule,), {
                        '__init__': make_init(filepath)
                     })
                     
                     # Set meta on the new class
                     DynamicModuleClass.meta = mod_meta

                except Exception as e:
                     print(f"Failed to load YAML module {filepath}: {e}")
                     continue

                self.register_tool("module", tool_id, DynamicModuleClass, aliases=[legacy_path])

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
                # Calculate legacy path for alias?
                rel_path = os.path.relpath(filepath, root_dir)
                base, _ = os.path.splitext(rel_path)
                legacy_path = "workflow/" + base.replace(os.path.sep, "/")
                
                try:
                     temp = WorkflowModule(filepath)
                     mod_meta = temp.meta.copy()
                     tool_id = mod_meta.get('id')
                     
                     if not tool_id:
                         tool_id = os.path.splitext(os.path.basename(filepath))[0]
                     
                     # Create Dynamic WorkflowModule
                     def make_init(path):
                        def __init__(self_inner):
                             WorkflowModule.__init__(self_inner, yaml_path=path)
                        return __init__
                    
                     safe_name = "DynamicWF_" + "".join(x for x in tool_id if x.isalnum())
                    
                     DynamicWorkflowClass = type(safe_name, (WorkflowModule,), {
                         '__init__': make_init(filepath)
                     })
                     DynamicWorkflowClass.meta = mod_meta
                
                except Exception as e:
                     print(f"Failed to load Workflow module {filepath}: {e}")
                     continue

                self.register_tool("workflow", tool_id, DynamicWorkflowClass, aliases=[legacy_path])

    def get_module(self, path: str):
        # 1. Exact match
        if path in self.modules:
            return self.modules[path]()
        
        # 2. Alias match
        if path in self.aliases:
            real_name = self.aliases[path]
            return self.modules[real_name]()
            
        # 3. Smart Lookup (User typed 'nmap' but we have '/module/nmap')
        # Try prepending /module/
        check_mod = f"/module/{path}"
        if check_mod in self.modules:
            return self.modules[check_mod]()
            
        # Try prepending /workflow/
        check_wf = f"/workflow/{path}"
        if check_wf in self.modules:
            return self.modules[check_wf]()
            
        return None

    def list_modules(self):
        return sorted(list(self.modules.keys()))

    def list_pure_modules(self):
        """Returns only standard modules (not workflows)."""
        return sorted([k for k in self.modules.keys() if not k.startswith("/workflow/")])

    def list_workflow_modules(self):
        """Returns only workflow modules."""
        return sorted([k for k in self.modules.keys() if k.startswith("/workflow/")])

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
