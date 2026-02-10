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
