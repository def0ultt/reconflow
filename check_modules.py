#!/usr/bin/env python3
"""Quick diagnostic to check module loading"""

from core.context import Context

print("Initializing Context...")
ctx = Context()

print(f"\nTotal modules loaded: {len(ctx.tool_manager.modules)}")
print(f"Module registry:")
for name, mod_class in ctx.tool_manager.modules.items():
    meta = getattr(mod_class, 'meta', {})
    print(f"  {name}")
    print(f"    ID: {meta.get('id', 'N/A')}")
    print(f"    Name: {meta.get('name', 'N/A')}")

print(f"\nModule list (via list_modules()):")
mod_list = ctx.tool_manager.list_modules()
for m in mod_list:
    print(f"  - {m}")

print(f"\nSearching for 'full-recon':")
results = ctx.tool_manager.search_modules('full-recon')
print(f"  Found {len(results)} results")
for idx, path, meta in results:
    print(f"    {path}: {meta.get('name')}")
