from fastapi import APIRouter, HTTPException, Depends
from typing import List
import shutil
import os
import uuid

from db.session import get_session
from projects.manager import ProjectManager
from server.schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate

router = APIRouter()

def get_project_manager():
    return ProjectManager()

@router.get("/", response_model=List[ProjectResponse])
def list_projects(manager: ProjectManager = Depends(get_project_manager)):
    """List all projects with basic stats."""
    projects = manager.list_projects()
    response = []
    for p in projects:
        stats = manager.get_project_stats(p.id)
        # Convert SQLAlchemy model to Pydantic
        p_dict = {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "path": p.path,
            "created_at": p.created_at,
            "stats": stats
        }
        response.append(p_dict)
    return response

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, manager: ProjectManager = Depends(get_project_manager)):
    """Create a new project or a temporary one."""
    if project.is_temp:
        # Create temp project
        unique_id = str(uuid.uuid4())[:8]
        project.name = f"temp-{unique_id}"
        project.path = f"/tmp/reconflow/{unique_id}"
        project.description = "Temporary Project"
    
    try:
        new_proj = manager.create_project(project.name, project.path)
        # return basic response
        return {
            "id": new_proj.id,
            "name": new_proj.name,
            "description": new_proj.description,
            "path": new_proj.path,
            "created_at": new_proj.created_at,
            "stats": {"file_count": 0, "total_size_bytes": 0}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{project_id}")
def delete_project(project_id: int, manager: ProjectManager = Depends(get_project_manager)):
    """Delete a project and its data."""
    success = manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": "Project deleted"}

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, manager: ProjectManager = Depends(get_project_manager)):
    """Get project details."""
    p = manager.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    stats = manager.get_project_stats(p.id)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "path": p.path,
        "created_at": p.created_at,
        "stats": stats
    }

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project: ProjectUpdate, manager: ProjectManager = Depends(get_project_manager)):
    """Update project details (Name, Path, Description)."""
    p = manager.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    if project.name:
        p.name = project.name
    if project.description:
        p.description = project.description
    if project.path:
        # TODO: Move files if path changes?
        # For now just updating the record.
        p.path = project.path
        
    try:
        manager.session.commit()
        manager.session.refresh(p)
        stats = manager.get_project_stats(p.id)
        return {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "path": p.path,
            "created_at": p.created_at,
            "stats": stats
        }
    except Exception as e:
        manager.session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
