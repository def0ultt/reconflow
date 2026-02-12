from tools.manager import ToolManager
from utils.paths import get_project_root

tm = ToolManager()
print("Loading modules...")
tm.load_yaml_modules(root_dirs=[str(get_project_root() / "modules")])

print(f"Loaded {len(tm.modules)} modules.")

first_key = list(tm.modules.keys())[0]
mod_cls = tm.modules[first_key]

print(f"First module: {first_key}")
print(f"Meta type: {type(mod_cls.meta)}")
print(f"Meta content: {mod_cls.meta}")
