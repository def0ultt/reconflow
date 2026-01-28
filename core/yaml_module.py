from typing import Any, Dict, List
import yaml
import subprocess
import os
from jinja2 import Template
from core.base import BaseModule, Option
from core.schema import validate_yaml, ModuleSchema

class GenericYamlModule(BaseModule):
    """
    A generic module that runs CLI tools defined in a YAML file.
    Strictly follows the new ModuleSchema.
    """
    def __init__(self, yaml_path: str = None):
        super().__init__()
        self.yaml_path = yaml_path
        self.schema: ModuleSchema = None
        
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def load_from_yaml(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"YAML module definitions not found at {path}")
        
        with open(path, 'r') as f:
            raw_data = yaml.safe_load(f)
            
        # Validate using Schema
        model = validate_yaml(raw_data)
        if not isinstance(model, ModuleSchema):
            raise ValueError(f"File {path} is not a Module (type={getattr(model, 'type', 'unknown')})")
        
        self.schema = model

        # 1. Parse Metadata (Info)
        self.meta.update({
            'name': self.schema.info.name,
            'description': self.schema.info.description,
            'author': self.schema.info.author,
            'id': self.schema.info.id
        })

        # 2. Parse Vars -> Options
        for name, config in self.schema.vars.items():
            self.options[name] = Option(
                name=name,
                value=config.default,
                required=config.required,
                description=f"Variable: {name}"
            )

    def run(self, context) -> Dict[str, Any]:
        """
        Execute the steps defined in the YAML Schema.
        Returns a dictionary of captured outputs.
        """
        if not self.schema:
            print("[!] No schema check loaded.")
            return {}

        outputs = {}
        
        # 1. Build initial render context
        # Base: Global Context (Secrets, Global Vars, System Vars)
        render_ctx = context.get_global_context()
        
        # Merge: Module Inputs (Options)
        # Options override globals if names collide
        inputs = {k: v.value for k, v in self.options.items()}
        render_ctx.update(inputs)
        
        # Also expose inputs under 'inputs' namespace for backward compatibility/clarity
        render_ctx['inputs'] = inputs
        
        runner_state = {
            'last_stdout': None
        }
        
        for step in self.schema.steps:
            step_id = step.name
            
            # --- Condition Check ---
            if step.condition:
                # Render condition first (to resolve vars)
                cond_str = Template(step.condition).render(render_ctx)
                try:
                    # simplistic eval
                    if not eval(cond_str):
                        print(f"[*] Skipping step '{step_id}' (Condition met: {cond_str})")
                        continue
                except Exception as e:
                    print(f"[!] condition evaluation failed for '{step_id}': {e}")
                    continue

            # --- Arguments ---
            args_template = step.args
            cmd_args = Template(args_template).render(render_ctx)
            
            full_cmd = f"{step.tool} {cmd_args}"
            print(f"[*] Executing step '{step_id}': {full_cmd}")
            
            # --- Output Path logic ---
            output_path = None
            copy_to_project = False
            
            if step.output:
                if step.output.path:
                    output_path = Template(step.output.path).render(render_ctx)
                    copy_to_project = True # Spec says if specific path, also take copy
                elif step.output.filename:
                     if context.current_project:
                        output_path = os.path.join(context.current_project.path, step.output.filename)
            
            # --- Timeout Parsing ---
            timeout_sec = None
            if step.timeout:
                try:
                    val = step.timeout.lower()
                    if val.endswith('m'):
                        timeout_sec = int(val[:-1]) * 60
                    elif val.endswith('h'):
                        timeout_sec = int(val[:-1]) * 3600
                    elif val.endswith('s'):
                        timeout_sec = int(val[:-1])
                    else:
                        timeout_sec = int(val)
                    
                    if timeout_sec <= 0:
                        print(f"[!] Invalid timeout value {timeout_sec} (must be > 0). Ignoring.")
                        timeout_sec = None
                except:
                    print(f"[!] Invalid timeout format '{step.timeout}', ignoring.")

            # --- Execution with Piping ---
            input_data = None
            if step.stdin and runner_state['last_stdout']:
                input_data = runner_state['last_stdout']

            try:
                proc = subprocess.run(
                    full_cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    input=input_data,
                    timeout=timeout_sec
                )
                
                # Update State
                if step.capture:
                     runner_state['last_stdout'] = proc.stdout
                else:
                     runner_state['last_stdout'] = None # Clear if not captured? Or keep? 
                     # Spec says "If true, engine saves... for subsequent".
                     # Implies if false, maybe not available for piping?
                     # Let's keep it in 'last_stdout' only if capture=True.
                     pass
                
                # --- Output Saving ---
                file_created_by_tool = False
                if output_path and os.path.exists(output_path):
                     # Tool seemingly created the file (or appended to it).
                     # We do NOT overwrite it with proc.stdout (which might be empty).
                     file_created_by_tool = True
                
                # 1. Write to specific path if tool didn't create it
                if output_path and not file_created_by_tool:
                    if proc.stdout:
                         # Ensure dirs
                         os.makedirs(os.path.dirname(output_path), exist_ok=True)
                         with open(output_path, 'w') as f:
                             f.write(proc.stdout)
                    else:
                         # Tool produced no output and no file?
                         pass
                
                # 2. Copy to project if needed
                if output_path and copy_to_project and context.current_project:
                    # Construct project path filename
                    fname = os.path.basename(output_path)
                    proj_path = os.path.join(context.current_project.path, fname)
                    
                    # If output_path exists (either tool created it or we wrote it)
                    if os.path.exists(output_path):
                        if os.path.abspath(proj_path) != os.path.abspath(output_path):
                             import shutil
                             shutil.copy(output_path, proj_path)
                    
                outputs[step_id] = output_path
                
                # Update Render Context
                render_ctx[step_id] = {
                    'stdout': proc.stdout,
                    'stderr': proc.stderr,
                    'output_file': output_path
                }
                
            except subprocess.TimeoutExpired:
                 print(f"[!] Step '{step_id}' timed out after {step.timeout}")
            except subprocess.CalledProcessError as e:
                print(f"[!] Error executing step {step_id}: {e}")
                print(e.stderr)
                # Continue or raise? Spec validation phase usually implies strictness.
                # But recon tools fail often (no results etc).
                # Probably should raise or define 'ignore_errors' (not in spec yet).
                raise e

        return outputs
