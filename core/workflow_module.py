from core.base import BaseModule, Option
from workflow.engine import WorkflowRunner
import yaml
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.context import Context
from workflow.engine import WorkflowRunner
import yaml
import os

class WorkflowModule(BaseModule):
    """
    Wraps a YAML workflow definition into a standard Module.
    Allows 'use workflow/xyz', 'set var val', 'run'.
    """
    def __init__(self, yaml_path: str = None):
        super().__init__()
        self.yaml_path = yaml_path
        self._wf_def = {}
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def load_from_yaml(self, path: str):
        if not os.path.exists(path):
            return # Should raise?
        
        with open(path, 'r') as f:
            self._wf_def = yaml.safe_load(f)

        # Meta
        meta = self._wf_def.get('metadata', {})
        self.meta.update({
            'name': meta.get('name', 'Unknown Workflow'),
            'description': meta.get('description', ''),
            'author': meta.get('author', 'Unknown'),
            'id': meta.get('id', 'workflow')
        })

        # Variables -> Options
        # We treat all top-level variables as settable options
        variables = self._wf_def.get('variables', {})
        for k, v in variables.items():
            self.options[k] = Option(
                name=k,
                value=v, # Default value from YAML
                required=True, # Assume required?
                description=f"Workflow variable: {k}"
            )

    def run(self, context: 'Context'):
        # Create inputs dict from current options
        inputs = {k: opt.value for k, opt in self.options.items()}
        
        # We need to run this specific workflow def.
        # WorkflowRunner normally loads by name from manager.
        # Here we have the definition directly.
        
        # We can bypass manager lookup by modifying runner or registering this temp?
        # Actually, if we are here, we are "using" this module.
        # Let's extend Runner to accept definition or ID.
        
        runner = WorkflowRunner(context)
        
        # We need to inject our workflow definition into the runner or pass it.
        # WorkflowRunner.run_workflow expects name and does: manager.get_workflow(name)
        # So we can ensure this workflow is in the manager?
        # OR we modify run_workflow to accept def.
        
        # Let's call internal method or modified public method
        print(f"[*] Executing Workflow Module: {self.meta['name']}")
        
        # We'll use a slightly hacky way if we don't want to change Runner signature too much,
        # but changing signature is better.
        # Since I can't easily change Runner in this file, I'll access the internal logic
        # by passing the definition to a new method I'll add to Runner or mimicking logic.
        
        # Better: Since "use workflow/xxx" was loaded from manager, it IS in the manager? 
        # Wait, if we register it as a module, it might not be in WorkflowManager unless we dual load.
        # Let's assuming we dual load.
        
        # Access ID
        wf_id = self._wf_def.get('metadata', {}).get('id')
        if not wf_id:
            # If loaded from custom file, might not match ID in manager if filenames differ?
            # Let's use the Runner's internal logic but adapted.
            pass

        # Re-implementing simplified runner call here to avoid dependency cycle or signature issues
        # Or better: Add run_workflow_def to WorkflowRunner
        runner.run_workflow_with_definition(self._wf_def, inputs)
