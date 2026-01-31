from core.base import BaseModule
from core.yaml_module import GenericYamlModule
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

    def _generate_full_name(self, tool_id: str) -> str:
        """
        Generates the full name for a tool.
        Format: /module/{id}
        """
        # We unified everything to 'module'
        return f"/module/{tool_id}"

    def register_tool(self, tool_type: str, tool_id: str, module_class, aliases: list = None):
        """
        Registers a tool (module) with a unique ID.
        Enforces naming convention and checks for duplicates.
        Can optionally register aliases (pointers to the full name).
        """
        # Force type to 'module' for internal consistency
        tool_type = "module"
        full_name = self._generate_full_name(tool_id)
        
        if full_name in self.modules:
            print(f"[-]Error: module with id '{tool_id}' already exists.")
            return

        self.modules[full_name] = module_class
        print(f"[+] Registered module: {full_name}")
        
        # Register Aliases
        if aliases:
            for alias in aliases:
                # Avoid overwriting modules with aliases if collision? 
                # Prioritize explicit registration.
                if alias not in self.modules and alias not in self.aliases:
                    self.aliases[alias] = full_name
                    # print(f"    (Alias: {alias})")

    def load_yaml_modules(self, root_dirs: list = None):
        """Scans for .yml files in specified directories and registers them."""
        if not root_dirs:
            root_dirs = ["modules", "workflows"] # default dirs
            
        patterns = []
        for d in root_dirs:
             patterns.append(os.path.join(d, "**", "*.yml"))
             patterns.append(os.path.join(d, "**", "*.yaml"))
        
        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                # Calculate legacy path for alias
                # We want to support 'modules/x/y' and 'workflows/x/y' as aliases?
                # Let's derive a relative identifier.
                # Find which root dir this file belongs to.
                
                legacy_path = None
                for d in root_dirs:
                     if filepath.startswith(d):
                         rel_path = os.path.relpath(filepath, d)
                         base, _ = os.path.splitext(rel_path)
                         legacy_path = f"{d}/{base}".replace(os.path.sep, "/")
                         
                         # Also support just the relative path inside the dir (e.g. 'custom/mytool')
                         # But collision risk.
                         break

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

                aliases = []
                if legacy_path:
                    aliases.append(legacy_path)
                    
                self.register_tool("module", tool_id, DynamicModuleClass, aliases=aliases)

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
            
        # Try prepending /workflow/ (legacy support for lookup)
        # Even though we register as module, maybe alias was registered as workflow/xxx?
        # Our loader registers legacy_path which includes the directory name ('workflow/xxx'). 
        # So alias match above covers it.
            
        return None

    def list_modules(self):
        return sorted(list(self.modules.keys()))

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
