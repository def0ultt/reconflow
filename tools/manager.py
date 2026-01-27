from core.base import BaseModule
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

    def get_module(self, path: str):
        module_cls = self.modules.get(path)
        if module_cls:
            return module_cls() # Return a new instance
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
