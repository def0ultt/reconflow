from typing import Any, Dict, List
import yaml
import subprocess
import os
from jinja2 import Template
from core.base import BaseModule, Option

class GenericYamlModule(BaseModule):
    """
    A generic module that runs CLI tools defined in a YAML file.
    """
    def __init__(self, yaml_path: str = None):
        super().__init__()
        self.yaml_path = yaml_path
        self._config = {}
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def load_from_yaml(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"YAML module definitions not found at {path}")
        
        with open(path, 'r') as f:
            self._config = yaml.safe_load(f)

        # 1. Parse Metadata
        meta = self._config.get('metadata', {})
        self.meta.update({
            'name': meta.get('name', 'Unknown YAML Module'),
            'description': meta.get('description', ''),
            'author': meta.get('author', 'Unknown'),
            'id': meta.get('id', 'yaml-module')
        })

        # 2. Parse Inputs -> Options
        # "inputs" in user example seems to be arguments provided at runtime
        # "variables" (vars) are global defaults
        
        # We map 'inputs' key from YAML to self.options
        inputs = self._config.get('inputs', {})
        for name, default_val in inputs.items():
            self.options[name] = Option(
                name=name,
                value=default_val,
                required=True, # Assume inputs are required unless default is provided
                description=f"Input for {name}"
            )
            
        # Also map 'variables' as options but maybe hidden or pre-filled?
        # For now, let's treat variables as internal context, but if user wants to override?
        # The user example shows 'variables' as global in workflow, but modules also have 'inputs'.
        # Let's stick to inputs for now.

    def run(self, context) -> Dict[str, Any]:
        """
        Execute the steps defined in the YAML.
        Returns a dictionary of captured outputs.
        """
        steps = self._config.get('steps', [])
        outputs = {}
        
        # Prepare context for Jinja2
        # It includes options values + any previously captured outputs
        # + global variables?
        
        # 1. Build initial render context
        render_ctx = {
            'inputs': {k: v.value for k, v in self.options.items()},
            # Add global context variables if needed, e.g. project_path
            'project_path': context.current_project.path if context.current_project else '/tmp'
        }
        
        # Also process top-level variables if any, resolving them against themselves?
        # simple resolution for now.
        
        for step in steps:
            step_id = step.get('id', step.get('name', 'unknown'))
            tool = step.get('tool')
            args_template = step.get('args', '')
            
            # Render arguments
            tmpl = Template(args_template)
            cmd_args = tmpl.render(render_ctx)
            
            full_cmd = f"{tool} {cmd_args}"
            print(f"[*] Executing step '{step_id}': {full_cmd}")
            
            # Identify where to save output if 'path' is defined in 'output' block
            output_def = step.get('output', {})
            output_file = output_def.get('path')
            
            if output_file:
                # Render output path as it might have {{variables}}
                output_file = Template(output_file).render(render_ctx)
                
            # Execution
            try:
                # If pipe is true, we might need complex handling. 
                # For now, standard subprocess run.
                
                # Check for stdin handling (not implemented yet for simplicity, or we can use input=...)
                
                proc = subprocess.run(
                    full_cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # stdout/stderr logging?
                # context.logger.debug(proc.stdout)
                
                # Handle Output Extraction
                # 1. If output is file:
                if output_file:
                    # Some tools don't write to file automatically, user might have used redirection > in args?
                    # Or rely on tool flags.
                    # If 'extract' is used, we might read the file or stdout.
                    outputs[step_id] = output_file
                    
                # 2. If capture output (stdout) specific logic?
                # Ensure we update render_ctx with this step's output so next steps can use it.
                # Example: {{steps.subdomain.output}}
                
                # Let's map outputs generically
                render_ctx[step_id] = {
                    'stdout': proc.stdout,
                    'stderr': proc.stderr,
                    'output_file': output_file
                }
                
                # Also generic "latest"?
                
            except subprocess.CalledProcessError as e:
                print(f"[!] Error executing step {step_id}: {e}")
                print(e.stderr)
                raise e

        return outputs
