from db.session import get_session
from db.models import Workspace
from utils.paths import get_results_dir

class WorkspaceManager:
    """
    Manage workspace scopes and result contexts.
    """
    def __init__(self):
        self.session = get_session()
        self.current_workspace = None

    def create_workspace(self, name: str) -> Workspace:
        existing = self.session.query(Workspace).filter_by(name=name).first()
        if existing:
            print(f"Workspace {name} already exists.")
            return existing
        
        results_path = get_results_dir() / name
        results_path.mkdir(exist_ok=True)
        
        new_ws = Workspace(name=name, path=str(results_path))
        self.session.add(new_ws)
        self.session.commit()
        return new_ws

    def load_workspace(self, name: str) -> Workspace:
        workspace = self.session.query(Workspace).filter_by(name=name).first()
        if workspace:
            self.current_workspace = workspace
        return workspace
        
    def list_workspaces(self):
        return self.session.query(Workspace).all()
