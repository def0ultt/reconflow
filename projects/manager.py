from db.session import get_session
from db.models import Project
from utils.paths import get_results_dir

class ProjectManager:
    """
    Manage project scopes and result contexts.
    """
    def __init__(self):
        self.session = get_session()
        self.current_project = None

    def create_project(self, name: str, path: str = None) -> Project:
        existing = self.session.query(Project).filter_by(name=name).first()
        if existing:
            print(f"Project {name} already exists.")
            return existing
        
        if path:
             # Use custom path from user
             import pathlib
             results_path = pathlib.Path(path).expanduser().resolve()
        else:
             results_path = get_results_dir() / "projects" / name
             
        results_path.mkdir(parents=True, exist_ok=True)
        
        new_proj = Project(name=name, path=str(results_path))
        self.session.add(new_proj)
        self.session.commit()
        return new_proj

    def load_project(self, name: str) -> Project:
        project = self.session.query(Project).filter_by(name=name).first()
        if project:
            self.current_project = project
        return project
        
    def list_projects(self):
        return self.session.query(Project).all()

    def get_project_by_id(self, project_id: int) -> Project:
        return self.session.query(Project).filter(Project.id == project_id).first()

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project_by_id(project_id)
        if not project:
            return False
            
        # Delete from DB
        self.session.delete(project)
        self.session.commit()
        
        # Optional: Delete from Filesystem (if we want to be destructive)
        # For now, let's keep the files for safety or make it an option?
        # User said: "Remove project and its data". So we should delete.
        import shutil
        import os
        if os.path.exists(project.path):
            try:
                shutil.rmtree(project.path)
            except Exception as e:
                print(f"Error deleting path {project.path}: {e}")
        
        return True

    def get_project_stats(self, project_id: int) -> dict:
        project = self.get_project_by_id(project_id)
        if not project:
            return {"file_count": 0, "total_size_bytes": 0}
            
        # Count files and size in project path
        count = 0
        size = 0
        import os
        if os.path.exists(project.path):
            for root, dirs, files in os.walk(project.path):
                count += len(files)
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        size += os.path.getsize(fp)
                    except:
                        pass
                        
        return {
            "file_count": count, 
            "total_size_bytes": size,
            "last_modified": project.created_at # Or actual FS modified time
        }
