from config.loader import load_config
from workspaces.manager import WorkspaceManager
from tools.manager import ToolManager
from workflow.manager import WorkflowManager
from core.session_manager import SessionManager
from utils.logger import setup_logger

class Context:
    """
    Manages the current execution context (active workspace, workflow state).
    """
    def __init__(self):
        self.logger = setup_logger()
        self.config = load_config()
        
        # Managers
        self.workspace_manager = WorkspaceManager()
        self.tool_manager = ToolManager()
        
        # Register default modules (Manual for now, can be automated later)
        from recon.passive.subdomain_enum import SubdomainEnumModule
        self.tool_manager.register_module('scan/subdomain/passive', SubdomainEnumModule)

        self.workflow_manager = WorkflowManager()
        self.session_manager = SessionManager()
        
        # State
        self.current_workspace = None
        self.active_module = None
