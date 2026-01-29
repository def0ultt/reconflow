from typing import Any, Dict, List, Set, Optional
import yaml
import subprocess
import os
import concurrent.futures
import threading
import time
from jinja2 import Environment, StrictUndefined
from core.base import BaseModule, Option
from core.schema import validate_yaml, ModuleSchema

class GenericYamlModule(BaseModule):
    """
    A unified module that runs CLI tools or other modules defined in a YAML file.
    Implements DAG-based execution with dependencies and parallelism.
    """
    def __init__(self, yaml_path: str = None):
        super().__init__()
        self.yaml_path = yaml_path
        self.schema: ModuleSchema = None
        self._execution_results = {} # Stores output of executed steps: {step_name: output_data}
        self._lock = threading.Lock() # For thread-safe updates to results
        
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def _render_template(self, template_str, context):
        if not template_str: return ""
        env = Environment(undefined=StrictUndefined)
        return env.from_string(template_str).render(context)

    def load_from_yaml(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"YAML module definitions not found at {path}")
        
        with open(path, 'r') as f:
            raw_data = yaml.safe_load(f)
            
        # Validate using Schema
        model = validate_yaml(raw_data)
        
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
        Execute the steps defined in the YAML Schema using a DAG scheduler.
        Returns a dictionary of captured outputs.
        """
        if not self.schema:
            print("[!] No schema loaded.")
            return {}

        # 1. Prepare Context (Strict Scoping)
        render_ctx = {}
        
        # Inject Vars
        for name, opt in self.options.items():
            if opt.required and opt.value is None:
                raise ValueError(f"Variable '{name}' is required but has no value.")
            
            if opt.value is not None:
                render_ctx[name] = opt.value

        # 2. Build Dependency Graph
        steps_map = {step.name: step for step in self.schema.steps}
        dependencies = {step.name: set(step.depends_on) for step in self.schema.steps}
        
        self._execution_results = {}
        completed_steps = set()
        failed_steps = set()
        
        pending_steps = list(steps_map.keys())
        running_futures = {} # future -> step_name

        max_workers = 10 
        if 'threads' in render_ctx:
             try:
                 max_workers = int(render_ctx['threads'])
             except:
                 pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            while pending_steps or running_futures:
                # 1. Check for completed futures
                done, _ = concurrent.futures.wait(
                    running_futures.keys(), 
                    timeout=0.5, 
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    step_name = running_futures.pop(future)
                    try:
                        result = future.result()
                        # Result logic (store output)
                        with self._lock:
                            self._execution_results[step_name] = result
                            completed_steps.add(step_name)
                            
                            step_ctx = {
                                'output': result.get('output_file'),
                                'stdout': result.get('stdout'),
                                'stderr': result.get('stderr')
                            }
                            render_ctx[step_name] = step_ctx
                            
                    except Exception as e:
                        print(f"[!] Step '{step_name}' failed: {e}")
                        failed_steps.add(step_name)

                # 2. Submit new steps
                submission_list = []
                for step_name in pending_steps[:]:
                    deps = dependencies[step_name]
                    if deps.issubset(completed_steps):
                        # Ready to run!
                        step = steps_map[step_name]
                        
                        can_run = True
                        if not step.parallel and running_futures:
                             can_run = len(running_futures) == 0
                        
                        if can_run:
                            for running_step_name in running_futures.values():
                                r_step = steps_map[running_step_name]
                                if not r_step.parallel:
                                    can_run = False
                                    break
                                    
                        if can_run:
                            pending_steps.remove(step_name)
                            step_context = render_ctx.copy()
                            future = executor.submit(self._execute_step, step, step_context, context)
                            running_futures[future] = step_name
                
                if not running_futures and pending_steps:
                    print("[!] Deadlock or Dependency Failure detected.")
                    print(f"Pending: {pending_steps}")
                    print(f"Failed: {failed_steps}")
                    break

        return self._execution_results

    def _execute_step(self, step, render_ctx, full_context):
        """
        Executes a single step (Tool or Module).
        """
        step_id = step.name
        
        # 1. Condition Check
        if step.condition:
            try:
                cond_str = self._render_template(step.condition, render_ctx)
                if not eval(cond_str):
                    print(f"[*] Skipping step '{step_id}' (Condition met: {cond_str})")
                    return {'skipped': True, 'stdout': '', 'output_file': None}
            except Exception as e:
                print(f"[!] Condition evaluation failed for '{step_id}': {e}")
                return {'skipped': True, 'error': str(e)}

        # 2. Resolve Arguments
        try:
            cmd_args = self._render_template(step.args, render_ctx)
        except Exception as e:
             print(f"[!] Template rendering failed for arguments in '{step_id}': {e}")
             raise e 

        # 3. Execute
        if step.tool:
            return self._run_tool(step, cmd_args, render_ctx, full_context)
        elif step.module:
            return self._run_submodule(step, cmd_args, render_ctx, full_context)
        else:
            raise ValueError(f"Step '{step_id}' has neither tool nor module.")

    def _run_tool(self, step, cmd_args, render_ctx, full_context):
        step_id = step.name
        
        # Custom Path Logic
        tool_cmd = step.tool
        if step.path:
            try:
                custom_path = self._render_template(step.path, render_ctx)
            except Exception as e:
                raise ValueError(f"Failed to render path for step '{step_id}': {e}")

            if not os.path.exists(custom_path):
                 raise FileNotFoundError(f"Tool path not found: {custom_path}")
            tool_cmd = custom_path
            
        full_cmd = f"{tool_cmd} {cmd_args}"
        print(f"[*] Executing Tool '{step_id}': {full_cmd}")

        # Output Path Logic
        output_path = None
        if step.output:
            if step.output.path:
                try:
                    output_path = self._render_template(step.output.path, render_ctx)
                except Exception:
                     pass 
            elif step.output.filename:
                 if full_context.current_project:
                    output_path = os.path.join(full_context.current_project.path, step.output.filename)

        # Stdin Logic
        input_data = None
        if step.stdin and step.depends_on:
             last_dep = step.depends_on[-1] 
             if last_dep in render_ctx and 'stdout' in render_ctx[last_dep]:
                 input_data = render_ctx[last_dep]['stdout']

        # Timeout
        timeout_sec = self._parse_timeout(step.timeout)

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
            
            # Handle Output
            self._handle_output_file(output_path, proc.stdout, full_context)

            return {
                'stdout': proc.stdout,
                'stderr': proc.stderr,
                'output_file': output_path,
                'return_code': proc.returncode
            }

        except subprocess.CalledProcessError as e:
            print(f"[!] Error executing tool step {step_id}: {e}")
            raise e 

    def _run_submodule(self, step, cmd_args, render_ctx, full_context):
        step_id = step.name
        mod_ref = step.module
        print(f"[*] Executing Submodule '{step_id}': {mod_ref}")
        
        # 1. Resolve Module
        target_mod = None
        possible_path = mod_ref
        if not os.path.isabs(possible_path):
             if os.path.exists(possible_path):
                 target_mod = GenericYamlModule(possible_path)
             elif os.path.exists(os.path.join("modules", possible_path)):
                 target_mod = GenericYamlModule(os.path.join("modules", possible_path))

        if not target_mod:
             try:
                 if hasattr(full_context, 'tool_manager'):
                     target_mod = full_context.tool_manager.get_module(mod_ref)
             except ImportError:
                 pass
        
        if not target_mod:
            raise ValueError(f"Could not find module '{mod_ref}'")

        # 2. Pass Inputs
        for key, opt in target_mod.options.items():
            if key in render_ctx:
                target_mod.update_option(key, render_ctx[key])
        
        # 3. Execute recursively
        results = target_mod.run(full_context)
        
        return {
            'module_results': results,
            'stdout': str(results), 
            'output_file': None 
        }

    def _parse_timeout(self, timeout_str):
        if not timeout_str: return None
        try:
            val = timeout_str.lower()
            if val.endswith('m'): return int(val[:-1]) * 60
            if val.endswith('h'): return int(val[:-1]) * 3600
            if val.endswith('s'): return int(val[:-1])
            return int(val)
        except:
             return None

    def _handle_output_file(self, output_path, content, context):
        if not output_path or not content:
            return
            
        # Write to path
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"[!] Failed to write output to {output_path}: {e}")

        # Copy to project
        if context.current_project:
            fname = os.path.basename(output_path)
            proj_path = os.path.join(context.current_project.path, fname)
            if os.path.abspath(proj_path) != os.path.abspath(output_path):
                 import shutil
                 try:
                     shutil.copy(output_path, proj_path)
                 except:
                     pass
