from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import os
from pathlib import Path
from db import models
from db.session import get_session
from projects.manager import ProjectManager

router = APIRouter()

def get_project_manager():
    return ProjectManager()

@router.get("/{project_id}/artifacts")
def list_artifacts(project_id: int, manager: ProjectManager = Depends(get_project_manager)):
    """
    List all artifacts (files) in the project directory.
    Returns a list of file metadata.
    """
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project_path = Path(project.path)
    if not project_path.exists():
        return []

    artifacts = []
    # Walk through the project directory
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(project_path)
            
            # Skip hidden files or specific system files if needed
            if file.startswith('.'):
                continue
                
            artifacts.append({
                "name": file,
                "path": str(rel_path),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
                "type": file_path.suffix.lower().lstrip('.') or 'unknown'
            })
            
    return artifacts

@router.get("/{project_id}/artifacts/{file_path:path}")
def get_artifact_content(project_id: int, file_path: str, manager: ProjectManager = Depends(get_project_manager)):
    """
    Get the content of a specific artifact.
    Attempts to parse JSON if allowed, otherwise returns text or raw.
    """
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project_root = Path(project.path).resolve()
    target_path = (project_root / file_path).resolve()
    
    # Security check: Ensure target_path is within project_root
    if not str(target_path).startswith(str(project_root)):
        raise HTTPException(status_code=403, detail="Access denied: Path traversal detected")
        
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine content type mechanism
    # For now, we mainly want to support JSON for the tables, and maybe text/log.
    suffix = target_path.suffix.lower()
    
    try:
        if suffix == '.json':
            import json
            with open(target_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return {"type": "json", "content": content}
        elif suffix in ['.txt', '.log', '.md', '.csv', '.yml', '.yaml']:
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return {"type": "text", "content": content}
        else:
            return {"type": "binary", "message": "Binary file content not shown"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
