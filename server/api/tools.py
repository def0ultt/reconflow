from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
import shutil

from db.session import get_session
from db.repositories.tool_repo import ToolRepository
from server.schemas.tool import ToolCreate, ToolUpdate, ToolResponse

router = APIRouter()


def _get_repo():
    session = get_session()
    return ToolRepository(session)


def _tool_to_response(tool) -> dict:
    """Convert a Tool ORM object to a response dict, parsing JSON fields."""
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "binary_path": tool.binary_path,
        "command_template": tool.command_template,
        "default_args": json.loads(tool.default_args) if tool.default_args else [],
        "category": tool.category,
        "tags": json.loads(tool.tags) if tool.tags else [],
        "inputs": json.loads(tool.inputs) if tool.inputs else [],
        "outputs": json.loads(tool.outputs) if tool.outputs else [],
        "icon": tool.icon,
        "author": tool.author,
        "is_active": tool.is_active,
    }


@router.get("/", response_model=List[ToolResponse])
def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    active_only: bool = Query(True, description="Only show active tools"),
):
    """List all tool templates, with optional filtering."""
    repo = _get_repo()
    tools = repo.get_all(limit=500)

    results = []
    for t in tools:
        if active_only and not t.is_active:
            continue
        if category and t.category != category:
            continue
        if search:
            q = search.lower()
            name_match = q in (t.name or "").lower()
            desc_match = q in (t.description or "").lower()
            tag_match = q in (t.tags or "").lower()
            if not (name_match or desc_match or tag_match):
                continue
        results.append(_tool_to_response(t))

    return results


@router.get("/categories")
def list_categories():
    """List all distinct tool categories."""
    repo = _get_repo()
    tools = repo.get_all(limit=500)
    cats = sorted(set(t.category for t in tools if t.category))
    return cats


@router.post("/", response_model=ToolResponse)
def create_tool(tool: ToolCreate):
    """Import/create a new tool template."""
    repo = _get_repo()

    # Check for duplicate name
    existing = repo.get_by_name(tool.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Tool '{tool.name}' already exists")

    tool_data = {
        "name": tool.name,
        "description": tool.description,
        "binary_path": tool.binary_path,
        "command_template": tool.command_template,
        "default_args": json.dumps(tool.default_args) if tool.default_args else None,
        "category": tool.category,
        "tags": json.dumps(tool.tags) if tool.tags else None,
        "inputs": json.dumps([i.dict() for i in tool.inputs]) if tool.inputs else None,
        "outputs": json.dumps([o.dict() for o in tool.outputs]) if tool.outputs else None,
        "icon": tool.icon,
        "author": "user",
        "is_active": True,
    }

    created = repo.create(tool_data)
    return _tool_to_response(created)


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: int):
    """Get a single tool template by ID."""
    repo = _get_repo()
    tool = repo.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return _tool_to_response(tool)


@router.put("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: int, tool_update: ToolUpdate):
    """Update an existing tool template."""
    repo = _get_repo()
    tool = repo.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    update_data = {}
    if tool_update.name is not None:
        update_data["name"] = tool_update.name
    if tool_update.description is not None:
        update_data["description"] = tool_update.description
    if tool_update.binary_path is not None:
        update_data["binary_path"] = tool_update.binary_path
    if tool_update.command_template is not None:
        update_data["command_template"] = tool_update.command_template
    if tool_update.default_args is not None:
        update_data["default_args"] = json.dumps(tool_update.default_args)
    if tool_update.category is not None:
        update_data["category"] = tool_update.category
    if tool_update.tags is not None:
        update_data["tags"] = json.dumps(tool_update.tags)
    if tool_update.inputs is not None:
        update_data["inputs"] = json.dumps([i.dict() for i in tool_update.inputs])
    if tool_update.outputs is not None:
        update_data["outputs"] = json.dumps([o.dict() for o in tool_update.outputs])
    if tool_update.icon is not None:
        update_data["icon"] = tool_update.icon
    if tool_update.is_active is not None:
        update_data["is_active"] = tool_update.is_active

    updated = repo.update(tool, update_data)
    return _tool_to_response(updated)


@router.delete("/{tool_id}")
def delete_tool(tool_id: int):
    """Delete a tool template."""
    repo = _get_repo()
    success = repo.delete(tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "success", "message": "Tool deleted"}


@router.post("/{tool_id}/validate")
def validate_tool_binary(tool_id: int):
    """Check if the tool's binary exists on the server."""
    repo = _get_repo()
    tool = repo.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if not tool.binary_path:
        return {"valid": False, "message": "No binary path configured"}

    # Check if binary exists in PATH or as absolute path
    found = shutil.which(tool.binary_path)
    return {
        "valid": found is not None,
        "resolved_path": found,
        "message": f"Found at {found}" if found else f"'{tool.binary_path}' not found in PATH"
    }
