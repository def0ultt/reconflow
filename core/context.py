from config.loader import load_config
from projects.manager import ProjectManager
from tools.manager import ToolManager
from workflow.manager import WorkflowManager
from utils.logger import setup_logger

class Context:
    """
    Manages the current execution context (active project, workflow state).
    """
    def __init__(self):
        self.logger = setup_logger()
        self.config = load_config()
        
        # Managers
        self.project_manager = ProjectManager()
        self.tool_manager = ToolManager()
        
        # Register default modules (Manual for now, can be automated later)
        from recon.passive.subdomain_enum import SubdomainEnumModule
        self.tool_manager.register_module('scan/subdomain/passive', SubdomainEnumModule)

        self.workflow_manager = WorkflowManager()
        
        # State
        self.current_project = None
        self.active_module = None
