from config.loader import load_config
from utils.paths import get_project_root
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
        
        # Load YAML modules
        self.tool_manager.load_yaml_modules(root_dir=str(get_project_root() / "modules"))
        self.tool_manager.load_workflow_modules(root_dir=str(get_project_root() / "workflows"))
        
        # Register default modules (Manual for now, can be automated later)
        from recon.passive.subdomain_enum import SubdomainEnumModule
        # Properly register the python module with an ID
        self.tool_manager.register_tool('module', 'subdomain-enum', SubdomainEnumModule, aliases=['scan/subdomain/passive'])

        self.workflow_manager = WorkflowManager()
        self.session_manager = SessionManager()
        
        # State
        self.current_project = None
        self.active_module = None
        
        # UI Selection State
        self.last_shown_map = []  # List of paths corresponding to IDs displayed
        self.last_shown_type = None # 'module' or 'workflow'

    def get_global_context(self) -> dict:
        """
        Returns a dictionary of global variables, secrets, and system info.
        Used for Jinja2 rendering in modules.
        """
        from datetime import datetime
        
        # 1. System Vars
        ctx = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'tmp': '/tmp', # Could be configurable
        }
        
        # 2. Project Context
        if self.current_project:
            ctx['project_path'] = self.current_project.path
            # For compatibility with user spec {{output_name}} behavior?
            # User spec says {{output_name}} is usually derived from module name.
            # That's local to module, not global.
        
        # 3. Settings (Global Vars + Secrets)
        # Global Vars ($proxy -> proxy)
        pid = self.current_project.id if self.current_project else None
        
        # Secrets
        secrets = self.settings_manager.get_all_secrets()
        ctx.update(secrets)
        
        # Vars (Priority to project specific)
        vars_dict = self.settings_manager.get_global_vars_dict(project_id=pid)
        ctx.update(vars_dict)
        
        return ctx
