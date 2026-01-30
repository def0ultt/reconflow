from typing import Any, Dict, List, Set, Optional
import yaml
import subprocess
import os
import concurrent.futures
import threading
import time
import json
from datetime import datetime
from jinja2 import Environment, StrictUndefined
from core.base import BaseModule, Option
from core.schema import validate_yaml, ModuleSchema
from utils.progress import ProgressTracker
from utils.output_formatter import (
    format_tool_execution,
    format_output_saved,
    format_command_error,
    format_deadlock_error,
    format_step_skipped,
    console
)

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
                description=f"Variable: {name}",
                metadata={
                    'type': config.type,
                    'flag': config.flag
                }
            )

    def run(self, context) -> Dict[str, Any]:
        """
        Execute the steps defined in the YAML Schema using a DAG scheduler.
        Returns a dictionary of captured outputs.
        """
        if not self.schema:
            print("[!] No schema loaded.")
            return {}

        # Initialize progress tracker
        total_steps = len(self.schema.steps)
        progress = ProgressTracker(total_steps)
        progress.start()

        # 1. Prepare Context (Strict Scoping)
        render_ctx = {}
        
        # Inject Vars
        for name, opt in self.options.items():
            if opt.required and opt.value is None:
                raise ValueError(f"Variable '{name}' is required but has no value.")
            
            if opt.value is not None:
                # Check if boolean variable
                var_type = opt.metadata.get('type', 'string')
                
                if var_type == "boolean":
                    # Inject flag if True, empty string if False
                    if opt.value is True:
                        flag = opt.metadata.get('flag', '')
                        render_ctx[name] = flag
                    else:
                        render_ctx[name] = ""
                else:
                    # Regular string variable
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

        try:
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
                                
                                # Update progress
                                progress.update(len(completed_steps))
                                
                        except Exception as e:
                            # Format professional error message
                            failed_steps.add(step_name)
                            # Still count as progress (failed but completed)
                            progress.update(len(completed_steps) + len(failed_steps))

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
                        format_deadlock_error(pending_steps, failed_steps)
                        break

            # Mark as complete
            progress.complete()
            
        except Exception as e:
            # Ensure progress tracker stops on error
            progress.stop()
            raise e

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
                    format_step_skipped(step_id, cond_str)
                    return {'skipped': True, 'stdout': '', 'output_file': None}
            except Exception as e:
                console.print(f"[red]⚠️  Condition evaluation failed for '{step_id}': {e}[/red]")
                return {'skipped': True, 'error': str(e)}

        # 2. Resolve Arguments
        try:
            cmd_args = self._render_template(step.args, render_ctx)
        except Exception as e:
             console.print(f"[red]❌ Template rendering failed for arguments in '{step_id}': {e}[/red]")
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
        
        # Format professional tool execution message
        format_tool_execution(step_id, tool_cmd, full_cmd)

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

        start_time = time.time()
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
            duration = time.time() - start_time
            
            # AUTOMATIC OUTPUT SAVING (ALWAYS)
            auto_output_path = self._get_auto_output_path(step, full_context)
            if auto_output_path:
                self._save_step_output(
                    auto_output_path, 
                    proc.stdout, 
                    proc.stderr, 
                    step, 
                    duration,
                    full_cmd
                )
                # Show save confirmation
                format_output_saved(auto_output_path)
            
            # Handle user-specified output (backward compatibility)
            if output_path:
                self._handle_output_file(output_path, proc.stdout, full_context)

            return {
                'stdout': proc.stdout,
                'stderr': proc.stderr,
                'output_file': auto_output_path or output_path,
                'return_code': proc.returncode
            }

        except subprocess.CalledProcessError as e:
            # Format professional error message
            format_command_error(step_id, e, full_cmd)
            raise e 

    def _run_submodule(self, step, cmd_args, render_ctx, full_context):
        step_id = step.name
        mod_ref = step.module
        console.print(f"\n🔧 [bold cyan]Running Submodule:[/bold cyan] [yellow]{mod_ref}[/yellow]")
        
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
            console.print(f"[red]⚠️  Failed to write output to {output_path}: {e}[/red]")

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

    def _get_auto_output_path(self, step, context):
        """Generate automatic output path for step execution"""
        if not context or not hasattr(context, 'current_project') or not context.current_project:
            return None
        
        project_path = context.current_project.path
        module_id = self.meta.get('id', 'unknown')
        step_name = step.name
        
        # Create module directory
        module_dir = os.path.join(project_path, module_id)
        os.makedirs(module_dir, exist_ok=True)
        
        # Generate output filename
        output_file = f"{step_name}.txt"
        return os.path.join(module_dir, output_file)
    
    def _save_step_output(self, path, stdout, stderr, step, duration, command):
        """Save step output with metadata"""
        try:
            # Save main output
            with open(path, 'w') as f:
                if stdout:
                    f.write(stdout)
                if stderr:
                    f.write("\n\n--- STDERR ---\n")
                    f.write(stderr)
            
            # Calculate line count
            line_count = 0
            if stdout:
                line_count = len(stdout.splitlines())
            
            # Save metadata
            metadata = {
                'step_name': step.name,
                'module_id': self.meta.get('id', 'unknown'),
                'module_name': self.meta.get('name', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': round(duration, 2),
                'line_count': line_count,
                'file_size': os.path.getsize(path),
                'command': command,
                'exit_code': 0
            }
            
            meta_path = path.replace('.txt', '.meta.json')
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            # Retry once
            try:
                time.sleep(0.5)
                with open(path, 'w') as f:
                    if stdout:
                        f.write(stdout)
                    if stderr:
                        f.write("\n\n--- STDERR ---\n")
                        f.write(stderr)
            except Exception as retry_error:
                console.print(f"[red]⚠️  Failed to save output: {retry_error}[/red]")
