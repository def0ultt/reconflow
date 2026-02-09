from typing import Any, Dict, List, Set, Optional
import sys
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
from core.parser import OutputParser
from parsers.builtin import BUILTIN_PARSERS
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
        
        # Initialize parser with built-in parsers
        self.parser = OutputParser()
        self.parser.builtin_parsers = BUILTIN_PARSERS.copy()
        
        if yaml_path:
            self.load_from_yaml(yaml_path)

    def _render_template(self, template_str, context):
        if not template_str: return ""
        
        # Preprocess conditionals: {-l {{targets}} || -h {{target}} }
        template_str = self._preprocess_conditionals(template_str, context)
        
        env = Environment(undefined=StrictUndefined)
        return env.from_string(template_str).render(context)

    def _preprocess_conditionals(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Pre-process conditional arguments in format: {-l {{targets}} || -h {{target}} }
        """
        import re
        result = []
        i = 0
        length = len(template_str)
        
        while i < length:
            # Check for start of conditional block: { followed by not {
            if template_str[i] == '{' and (i + 1 >= length or template_str[i+1] != '{'):
                start = i
                # Simple brace balance finder
                # Note: We need to properly skip Jinja {{ }} if they appear, but the simple counter
                # works if we assume balanced braces inside.
                
                depth = 1
                i += 1
                inner_start = i
                found_end = False
                
                while i < length:
                    char = template_str[i]
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            found_end = True
                            break
                    i += 1
                
                if found_end:
                    block_content = template_str[inner_start:i]
                    if '||' in block_content:
                         # Found conditional!
                        options = [opt.strip() for opt in block_content.split('||')]
                        selected_option = None
                        valid_found = False
                        
                        for option in options:
                            vars_needed = re.findall(r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}', option)
                            is_valid = True
                            if not vars_needed:
                                is_valid = True
                            else:
                                for var in vars_needed:
                                    val = context.get(var)
                                    # Check for Truthy (exists and not empty)
                                    if not val: 
                                        is_valid = False
                                        break
                            
                            if is_valid:
                                selected_option = option
                                valid_found = True
                                break
                        
                        if not valid_found:
                             # Strict Validation: Error if no option works
                             raise ValueError(f"Conditional argument failed: No valid option found in block '{{ {block_content} }}'. Ensure at least one variable is defined.")
                        
                        result.append(selected_option)
                    else:
                        # Just a regular single brace block
                        result.append(template_str[start:i+1])
                else:
                    # Incomplete brace
                    result.append(template_str[start:i])
            else:
                result.append(template_str[i])
            
            i += 1
            
        return "".join(result)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate condition with support for simplified syntax:
        - {var}        -> True if var exists and is truthy
        - {!var}       -> True if var is falsy or missing
        - {var == val} -> Equality check
        - {var != val} -> Inequality check
        """
        condition = condition.strip()
        
        # Check for simplified syntax { ... } but make sure it's not Jinja {{ ... }}
        if condition.startswith('{') and condition.endswith('}') and not condition.startswith('{{'):
            inner = condition[1:-1].strip()
            
            # Equality Check
            if '==' in inner:
                parts = inner.split('==')
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    target_val = parts[1].strip().strip("'").strip('"') # Remove quotes
                    actual_val = str(context.get(var_name, ''))
                    
                    # Handle boolean string comparison (e.g. 'True' == 'true')
                    if target_val.lower() in ('true', 'false') and actual_val.lower() in ('true', 'false'):
                         return target_val.lower() == actual_val.lower()
                         
                    return actual_val == target_val
            
            # Inequality Check
            elif '!=' in inner:
                parts = inner.split('!=')
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    target_val = parts[1].strip().strip("'").strip('"')
                    actual_val = str(context.get(var_name, ''))
                    
                    # Handle boolean string comparison
                    if target_val.lower() in ('true', 'false') and actual_val.lower() in ('true', 'false'):
                         return target_val.lower() != actual_val.lower()

                    return actual_val != target_val
            
            # Negation (Strictly Falsy or Missing)
            elif inner.startswith('!'):
                var_name = inner[1:].strip()
                val = context.get(var_name)
                return not val # Returns True if None, False, Empty String, etc.

            # Simple Truthiness
            else:
                var_name = inner
                val = context.get(var_name)
                return bool(val)

        # Fallback to standard Jinja + Eval
        cond_str = self._render_template(condition, context)
        return bool(eval(cond_str))

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
            'id': self.schema.info.id,
            'tag': self.schema.info.tag if self.schema.info.tag else ''
        })

        # 2. Parse Vars -> Options
        for name, config in self.schema.vars.items():
            self.options[name] = Option(
                name=name,
                value=config.default,
                required=config.required,
                description=config.description if config.description else "No description provided",
                metadata={
                    'type': config.type,
                    'flag': config.flag
                }
            )

    def run(self, context, background=False) -> Dict[str, Any]:
        """
        Execute the steps defined in the YAML Schema using a DAG scheduler.
        Returns a dictionary of captured outputs.
        """
        if not self.schema:
            print("[!] No schema loaded.")
            return {}

        # Initialize progress tracker (only if not in background)
        total_steps = len(self.schema.steps)
        progress = None
        
        if not background:
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
                    flag = opt.metadata.get('flag')
                    if flag:
                        # OLD BEHAVIOR: If flag defined, inject flag string
                        if opt.value is True:
                            render_ctx[name] = flag
                        else:
                            render_ctx[name] = ""
                    else:
                        # NEW BEHAVIOR: No flag defined, inject raw boolean
                        render_ctx[name] = opt.value
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
                                if progress:
                                    progress.update(len(completed_steps))
                                
                        except Exception as e:
                            # Format professional error message
                            failed_steps.add(step_name)
                            # Still count as progress (failed but completed)
                            if progress:
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
                                future = executor.submit(self._execute_step, step, step_context, context, background)
                                running_futures[future] = step_name
                    
                    if not running_futures and pending_steps:
                        format_deadlock_error(pending_steps, failed_steps)
                        break

            # Mark as complete
            if progress:
                progress.complete()
            
        except Exception as e:
            # Ensure progress tracker stops on error
            if progress:
                progress.stop()
            raise e

        return self._execution_results

    def _execute_step(self, step, render_ctx, full_context, background=False):
        """
        Executes a single step (Tool or Module).
        """
        step_id = step.name
        
        # 1. Condition Check
        if step.condition:
            try:
                should_run = self._evaluate_condition(step.condition, render_ctx)
                if not should_run:
                    format_step_skipped(step_id, step.condition)
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
            return self._run_tool(step, cmd_args, render_ctx, full_context, background=background)
        elif step.module:
            return self._run_submodule(step, cmd_args, render_ctx, full_context, background=background)
        else:
            raise ValueError(f"Step '{step_id}' has neither tool nor module.")

    def _run_tool(self, step, cmd_args, render_ctx, full_context, background=False):
        step_id = step.name
        
        # Custom Path Logic
        tool_cmd = step.tool
        
        # Built-in Tool Aliases
        # Allow usage of "json_parser" -> "python3 {root}/tools/json_parser.py"
        builtin_tools = {
            'json_parser': 'tools/json_parser.py',
            'xml_parser': 'tools/xml_parser.py'
        }
        
        if tool_cmd in builtin_tools:
            # Resolve absolute path relative to project root
            # Assuming file is in reconflow/core/yaml_module.py -> root is ../..
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tool_path = os.path.join(base_dir, builtin_tools[tool_cmd])
            
            if os.path.exists(tool_path):
                tool_cmd = f"{sys.executable} {tool_path}"
            else:
                 console.print(f"[yellow]⚠️  Built-in tool alias '{tool_cmd}' found but file missing at {tool_path}[/yellow]")
        
        if step.path:
            try:
                custom_path = self._render_template(step.path, render_ctx)
            except Exception as e:
                raise ValueError(f"Failed to render path for step '{step_id}': {e}")

            if not os.path.exists(custom_path):
                 raise FileNotFoundError(f"Tool path not found: {custom_path}")
            tool_cmd = custom_path
            
        full_cmd = f"{tool_cmd} {cmd_args}"
        
        if not background:
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
        
        # New "filename" field on step (takes precedence or works standalone)
        if step.filename:
            try:
                resolved_name = self._render_template(step.filename, render_ctx)
                
                # Strip quotes if present (common in conditional defaults)
                if resolved_name:
                    resolved_name = resolved_name.strip("'\"")

                if resolved_name and full_context.current_project:
                    output_path = os.path.join(full_context.current_project.path, resolved_name)
            except Exception as e:
                console.print(f"[red]⚠️  Failed to resolve filename for step '{step_id}': {e}[/red]")

        # Stdin Logic
        input_data = None
        if step.stdin and step.depends_on:
             # Aggregate stdout from ALL dependencies
             combined_input = []
             for dep_name in step.depends_on:
                 if dep_name in render_ctx and 'stdout' in render_ctx[dep_name]:
                     out = render_ctx[dep_name]['stdout']
                     if out:
                         combined_input.append(out)
             
             if combined_input:
                 input_data = "\n".join(combined_input)

        # Timeout
        timeout_sec = self._parse_timeout(step.timeout)

        # Determine working directory for tool execution
        # Tools should run from the project path, not reconflow installation path
        working_dir = None
        if full_context and hasattr(full_context, 'current_project') and full_context.current_project:
            working_dir = full_context.current_project.path
            # Ensure the project directory exists
            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)

        start_time = time.time()
        try:
            proc = subprocess.run(
                full_cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=timeout_sec,
                cwd=working_dir  # Execute from project directory
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
                if not background:
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

    def _run_submodule(self, step, cmd_args, render_ctx, full_context, background=False):
        step_id = step.name
        mod_ref = step.module
        
        if not background:
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
        results = target_mod.run(full_context, background=background)
        
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
        """Save step output with metadata and JSON parsing"""
        try:
            # 1. Save raw text output
            with open(path, 'w') as f:
                if stdout:
                    f.write(stdout)
                if stderr:
                    f.write("\n\n--- STDERR ---\n")
                    f.write(stderr)
            
            # 2. Parse output to JSON (server-side)
            tool_name = step.tool if step.tool else 'unknown'
            json_data = None
            
            if stdout and stdout.strip():
                json_data = self.parser.parse_to_json(stdout, tool_name)
            
            # 3. Save JSON if parsing successful
            has_json = False
            record_count = 0
            
            if json_data:
                json_path = path.replace('.txt', '.json')
                try:
                    with open(json_path, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    has_json = True
                    record_count = len(json_data)
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to save JSON: {e}[/yellow]")
            
            # 4. Calculate line count
            line_count = 0
            if stdout:
                line_count = len(stdout.splitlines())
            
            # 5. Save enhanced metadata
            metadata = {
                'step_name': step.name,
                'tool': tool_name,
                'module_id': self.meta.get('id', 'unknown'),
                'module_name': self.meta.get('name', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': round(duration, 2),
                'line_count': line_count,
                'file_size': os.path.getsize(path),
                'command': command,
                'exit_code': 0,
                'has_json': has_json,
                'record_count': record_count,
                'parser_used': tool_name if has_json else None
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

