from .context import Context
from .runner import Runner

class Engine:
    """
    Orchestrates execution and piping between tools.
    """
    def __init__(self, context: Context):
        self.context = context
        self.runner = Runner()

    def execute_workflow(self, workflow_name: str):
        workflow = self.context.workflow_manager.get_workflow(workflow_name)
        if not workflow:
            print(f" Workflow '{workflow_name}' not found")
            return
        
        print(f"🚀 Running workflow: {workflow_name}")
        for step in workflow:
            print(f"Executing: {step}")
            # Here we would actually dispatch commands. 
            # For now, we print. logic needs to be connected to CLI dispatch or ToolManager.
