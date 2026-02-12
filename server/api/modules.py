from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

class ModuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    tag: Optional[str] = None
    category: Optional[str] = None # Derived from path or meta
    inputs: List[Dict[str, Any]] = []

@router.get("/", response_model=List[ModuleResponse])
def list_modules(request: Request):
    """List all available modules."""
    tm = request.app.state.tool_manager
    modules = []
    
    # helper to get meta safely
    for path, mod_cls in tm.modules.items():
        meta = getattr(mod_cls, 'meta', {})
        
        # Extract inputs (arguments)
        # GenericYamlModule stores options in self.options but that requires instantiation.
        # However, 'arguments' are usually in meta if defined in YAML header?
        # Let's check a YAML file to see where args are defined.
        # Usually 'args' or 'options' property.
        # The meta dict usually contains top-level fields.
        
        # If args are not in meta, we might need to instantiate or parse them.
        # For now, let's just return basic info.
        
        mod_id = meta.get('id')
        if not mod_id:
            # Fallback to path name
            mod_id = path.split('/')[-1]

        modules.append({
            "id": mod_id,
            "name": meta.get('name', mod_id),
            "description": meta.get('description'),
            "author": meta.get('author'),
            "version": str(meta.get('version', '')),
            "tag": meta.get('tag'),
            # "inputs": meta.get('args', []) # Schema might differ
        })
        
    return modules
