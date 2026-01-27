from config.loader import load_config
from projects.manager import ProjectManager
from tools.manager import ToolManager
from workflow.manager import WorkflowManager
from core.session_manager import SessionManager
from utils.logger import setup_logger
from db.session import get_session
from db.repositories.project_repo import ProjectRepository
from core.file_manager import FileManager

class Context:
    """
    Manages the current execution context (active project, workflow state).
    """
    def __init__(self):
        self.logger = setup_logger()
        self.config = load_config()
        
        # Managers
        self.session_db = get_session()
        self.project_repo = ProjectRepository(self.session_db)
        self.file_manager = FileManager(self.project_repo)
        
        from core.settings_manager import SettingsManager
        self.settings_manager = SettingsManager(self.session_db)

        self.project_manager = ProjectManager() # Encapsulates some logic, but we might prefer repo
        self.tool_manager = ToolManager()
        
        # Register default modules (Manual for now, can be automated later)
        from recon.passive.subdomain_enum import SubdomainEnumModule
        self.tool_manager.register_module('scan/subdomain/passive', SubdomainEnumModule)

        self.workflow_manager = WorkflowManager()
        self.session_manager = SessionManager()
        
        # State
        self.current_project = None
        self.active_module = None
