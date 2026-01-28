
from core.base import BaseModule, Option
from workflow.engine import WorkflowRunner
import yaml
import os
from typing import TYPE_CHECKING, Any
from core.schema import validate_yaml, WorkflowSchema

if TYPE_CHECKING:
    from core.context import Context

class WorkflowModule(BaseModule):
    """
    Wraps a YAML workflow definition into a standard Module.
    Strictly follows the new WorkflowSchema.
    """
    def __init__(self, yaml_path: str = None):
        super().__init__()
        self.yaml_path = yaml_path
        self.schema: WorkflowSchema = None
        
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def load_from_yaml(self, path: str):
        if not os.path.exists(path):
            return 
        
        with open(path, 'r') as f:
            raw_data = yaml.safe_load(f)

        # Validate
        model = validate_yaml(raw_data)
        if not isinstance(model, WorkflowSchema):
             raise ValueError(f"File {path} is not a Workflow (type={getattr(model, 'type', 'unknown')})")
        
        self.schema = model

        # Meta
        self.meta.update({
            'name': self.schema.info.name,
            'description': self.schema.info.description,
            'author': self.schema.info.author,
            'id': self.schema.info.id
        })

        # Vars -> Options
        for name, config in self.schema.vars.items():
            self.options[name] = Option(
                name=name,
                value=config.default,
                required=config.required,
                description=f"Workflow variable: {name}"
            )

    def run(self, context: 'Context'):
        # Create inputs dict from current options
        inputs = {k: opt.value for k, opt in self.options.items()}
        
        runner = WorkflowRunner(context)
        print(f"[*] Executing Workflow Module: {self.meta['name']}")
        
        # Convert Schema back to dict for Runner
        # Note: Runner expects 'modules', 'metadata', 'variables'.
        # New Schema has 'workflow', 'info', 'vars'.
        # We must adapt it here or update Runner. 
        # Updating Runner is cleaner but might technically be "Phase 4". 
        # But to keep it working, I'll adapt the dict here temporarily or update Runner to check both.
        # Let's adapt here to minimize impact on Runner logic until Phase 4.
        
        wf_data = self.schema.model_dump()
        
        # Compatibility Adapter
        adapter = {
            'metadata': wf_data.get('info', {}),
            'variables': {k: v.get('default') for k, v in wf_data.get('vars', {}).items()},
            'modules': []
        }
        
        # Map steps from 'workflow' to 'modules'
        # Schema step: name, module, depends_on, inputs
        # Runner expects: id (name), module, depends_on, inputs
        for step in wf_data.get('workflow', []):
            adapter['modules'].append({
                'id': step['name'],
                'module': step['module'],
                'depends_on': step['depends_on'],
                'inputs': step['inputs']
            })

        runner.run_workflow_with_definition(adapter, inputs)

