import yaml
import os
from jinja2 import Template
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.context import Context

class WorkflowRunner:
    """
    Executes a YAML-defined workflow.
    """
    def __init__(self, context: 'Context'):
        self.context = context

    def run_workflow(self, workflow_name: str, inputs: dict = None):
        """
        Load and run a workflow by name (which acts as ID/Filename).
        """
        inputs = inputs or {}
        
        # 1. Load Workflow Definition
        wf_def = self.context.workflow_manager.get_workflow(workflow_name)
        if not wf_def:
             # Try loading from file directly if not in manager yet?
             # Or assume manager has it.
             print(f"Workflow '{workflow_name}' not found.")
             return

        # Handle simplified JSON storage vs YAML file loading
        # The user wants YAML files in workflows/ directory.
        # So we might need to adjust WorkflowManager or just load here.
        
        # If wf_def is list (old style) convert/reject?
        # New style is dict with 'modules' list.
        if isinstance(wf_def, list):
            print("Old style workflow (steplist) not supported by new engine.")
            return

        self._execute_logic(wf_def, inputs, workflow_name)

    def run_workflow_with_definition(self, wf_def: dict, inputs: dict = None):
        """
        Execute a workflow definition directly.
        """
        inputs = inputs or {}
        workflow_name = wf_def.get('metadata', {}).get('name', 'Direct Execution')
        print(f"[*] Starting Workflow: {workflow_name}")
        
        # Share logic with run_workflow? 
        # Refactor: extract common core.
        self._execute_logic(wf_def, inputs, workflow_name)

    def _execute_logic(self, wf_def, inputs, workflow_name):
        # 2. Initialize State
        wf_vars = wf_def.get('variables', {})
        state = {
            'input': inputs,
            'workspace': '/tmp',
        }
        for k, v in wf_vars.items():
            # Allow inputs to override workflow variables directly
            if k in inputs:
                state[k] = inputs[k]
                continue
                
            if isinstance(v, str):
                try:
                    state[k] = Template(v).render(state)
                except Exception:
                    state[k] = v
            else:
                state[k] = v
        
        # 3. Execution Graph
        modules_list = wf_def.get('modules', [])
        executed = set()
        outputs_store = {}
        mod_map = {m['id']: m for m in modules_list}
        
        while len(executed) < len(modules_list):
            progress = False
            for mod_def in modules_list:
                mid = mod_def['id']
                if mid in executed:
                    continue
                deps = mod_def.get('depends_on', [])
                if isinstance(deps, str): deps = [deps]
                if all(d in executed for d in deps):
                    print(f"[*] Running Workflow Step: {mid}")
                    self._run_step(mid, mod_def, state, outputs_store)
                    executed.add(mid)
                    progress = True
            if not progress:
                print("[!] Workflow Deadlock.")
                break
        print(f"[*] Workflow '{workflow_name}' completed.")

    def _run_step(self, mid, mod_def, state, outputs_store):
        # 1. Resolve Inputs
        # The module definition in workflow has 'inputs' mapping.
        # We need to render them using 'state' + 'outputs_store'
        
        # Update state with outputs from previous steps
        # User syntax: {{subdomain-enum.outputs.subdomains}}
        # So we need state['subdomain-enum'] = {'outputs': ...}
        
        # Prepare render context
        # We make a copy to avoid polluting global state effectively?
        # Or just update global state.
        
        # Flatten outputs for easy access? 
        # The user expects: {{step_id.outputs.var}}
        # So outputs_store should be {step_id: {'outputs': {key:val}}}
        
        render_ctx = state.copy()
        render_ctx.update(outputs_store)
        
        # Resolve 'inputs' block
        # inputs: 
        #   target: "{{target}}"
        step_inputs = {}
        raw_inputs = mod_def.get('inputs', {})
        
        for k, v in raw_inputs.items():
            if isinstance(v, str):
                step_inputs[k] = Template(v).render(render_ctx)
            else:
                step_inputs[k] = v
                
        # 2. Load Module
        module_path = mod_def.get('module')
        module = self.context.tool_manager.get_module(module_path)
        
        if not module:
            print(f"[!] Module '{module_path}' not found for step '{mid}'. Skipping.")
            return

        # 3. Apply Inputs to Module Options
        for opt_name, opt_val in step_inputs.items():
             module.update_option(opt_name, opt_val)
             
        # 4. Run Module
        try:
            # We assume GenericYamlModule returns a specific dict structure
            # But standard BaseModule.run() might not return anything?
            # We need to enforce return or standard capture.
            
            # For GenericYamlModule, we implemented it to return outputs dict.
            # For Standard Python modules, we might need to adopt a convention.
            
            res = module.run(self.context) 
            # res should be dict of outputs
            
            if res is None: res = {}
            
            # Store outputs
            # User syntax: outputs: subdomains: "{{workspace}}/subdomains.txt"
            # This implies the module MIGHT NOT return 'subdomains' key directly, 
            # but we define WHERE the output IS.
            
            # Actually, in generic yaml module: output is defined in module. 
            # In workflow: 'outputs' section maps workflow-vars to values?
            # No, looking at user example:
            # outputs:
            #   subdomains: "{{workspace}}/subdomains.txt"
            
            # This looks like defining variables for the NEXT steps to use.
            # So we resolve these values and store them in outputs_store[mid]['outputs']
            
            defined_outputs = mod_def.get('outputs', {})
            step_outputs = {}
            
            for out_key, out_val_tmpl in defined_outputs.items():
                 # Render the value (which is likely a path)
                 val = Template(out_val_tmpl).render(render_ctx)
                 step_outputs[out_key] = val
            
            # Merge with actual return values from module if any?
            # If the module returned data, we might want it.
            if isinstance(res, dict):
                step_outputs.update(res)

            outputs_store[mid] = {'outputs': step_outputs}
            print(f"    -> Step {mid} finished. Outputs: {list(step_outputs.keys())}")
            
        except Exception as e:
            print(f"[!] Step {mid} failed: {e}")
            raise e
