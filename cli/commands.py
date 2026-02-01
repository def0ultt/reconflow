from core.context import Context
from core.file_reader import FileReader
from utils.formatter import OutputFormatter
from rich.console import Console
from rich.table import Table
import os
from rich.text import Text
from rich import box
import shutil
import yaml
import json
from utils.paths import get_project_root

console = Console()
file_reader = FileReader()
formatter = OutputFormatter()


def cmd_use(ctx: Context, arg: str):
    if not arg:
        print("Usage: use <module_path>")
        return
    
    
    target_path = arg
    # Check if arg is an ID
    if arg.isdigit():
        idx = int(arg) - 1
        
        # Check context
        if not ctx.last_shown_map:
             print("[yellow]Please run 'show module' or 'show workflow' first (IDs change depending on context).[/yellow]")
             return
             
        if 0 <= idx < len(ctx.last_shown_map):
             target_path = ctx.last_shown_map[idx]
        else:
             print(f"[red]Invalid ID: {arg}. Range is 1-{len(ctx.last_shown_map)}[/red]")
             return
                 
    module = ctx.tool_manager.get_module(target_path)
    if module:
        ctx.active_module = module
        ctx.active_module_path = target_path
        # Pre-fill target if project is active ? 
        # For now, keep it simple.
    else:
        print(f" Module '{arg}' not found.")

def cmd_back(ctx: Context, arg: str):
    ctx.active_module = None
    ctx.active_module_path = None

def parse_boolean(value: str):
    """Parse string to boolean. Returns None if invalid."""
    val_lower = value.lower().strip()
    if val_lower in ('true', 'yes', '1', 'on'):
        return True
    elif val_lower in ('false', 'no', '0', 'off'):
        return False
    return None

def cmd_set(ctx: Context, arg: str):
    if not ctx.active_module:
        print("❌ No active module. Use 'use <module>' first.")
        return

    parts = arg.split(maxsplit=1)
    if len(parts) != 2:
        print("Usage: set <option> <value>")
        return
    
    opt, val = parts[0].lower(), parts[1]
    
    # Check if option exists
    if opt not in ctx.active_module.options:
        print(f"❌ Option '{opt}' not found.")
        return
    
    option_obj = ctx.active_module.options[opt]
    
    # Get variable type from metadata
    var_type = option_obj.metadata.get('type', 'string')
    
    # Handle boolean variables
    if var_type == "boolean":
        # Parse boolean value
        bool_val = parse_boolean(val)
        if bool_val is None:
            console.print(f"[red]Error: '{val}' is not a valid boolean value. Use: true, false, yes, no, 1, 0[/red]")
            return
        val = bool_val
    # Variable Substitution for string variables
    elif val.startswith('$'):
        var_key = val
        project_id = ctx.current_project.id if ctx.current_project else None
        resolved = ctx.settings_manager.get_variable(var_key, project_id)
        
        if resolved is not None:
            console.print(f"[dim]Resolved {var_key} -> {resolved}[/dim]")
            val = resolved
        else:
            console.print(f"[red]Error: Variable '{var_key}' not found.[/red]")
            return

    if ctx.active_module.update_option(opt, val):
        print(f"✅ {opt} => {val}")
    else:
        print(f"❌ Option '{opt}' not found.")
        

from cli.session_cmd import cmd_sessions
from cli.startup import run_settings_flow

def cmd_settings(ctx: Context, arg: str):
    run_settings_flow(ctx)


def cmd_run(ctx: Context, arg: str):
    if not ctx.active_module:
        print(" No active module.")
        return
    
    missing = ctx.active_module.validate_options()
    if missing:
        print(f" Missing required options: {', '.join(missing)}")
        return
    
    # Check for background flag
    run_in_background = False
    args = arg.split()
    if "-j" in args or "-d" in args:
        run_in_background = True
    
    if run_in_background:
        # Determine target for logging (heuristic)
        target = ctx.active_module.options.get('target', None)
        target_val = str(target.value) if target else "Unknown"
        
        session = ctx.session_manager.create_session(ctx.active_module, ctx, target_val)
        if session:
            console.print(f"[green]✓ Module '{ctx.active_module.meta['name']}' started in background (Session {session.id})[/green]")
            console.print(f"[dim]Type 'sessions' to view status.[/dim]")
    else:
        try:
            ctx.active_module.run(ctx)
        except Exception as e:
            print(f" Error running module: {e}")

def cmd_show(ctx: Context, arg: str):
    if not arg:
        print("Usage: show [options|modules|sessions|projects]")
        return
        
    if arg == 'options':
        if not ctx.active_module:
            print("No active module.")
            return
        
        table = Table(title=f"Module Options ({ctx.active_module.meta['name']})")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Current Setting", style="magenta")
        table.add_column("Required", style="green")
        table.add_column("Description", style="dim white")

        for name, opt in ctx.active_module.options.items():
            var_type = opt.metadata.get('type', 'string')
            
            # Format current value
            current_val = str(opt.value)
            if var_type == "boolean":
                flag = opt.metadata.get('flag')
                if flag and opt.value:
                    current_val = f"{opt.value} (flag: {flag})"
                else:
                    current_val = str(opt.value)
            
            table.add_row(
                name, 
                var_type,
                current_val, 
                str(opt.required), 
                opt.description
            )
        
        console.print(table)
    
    elif arg in ('modules', 'module'):
        cmd_list_modules(ctx, 'modules')

    elif arg == 'sessions':
        cmd_sessions(ctx, "-a")

    elif arg == 'projects':
        projects = ctx.project_manager.list_projects()
        if not projects:
            print("No projects found.")
            return

        table = Table(title="Projects", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", justify="center")
        table.add_column("Name", style="green", justify="center")
        table.add_column("Created At", style="magenta", justify="center")
        table.add_column("Status", style="yellow", justify="center")

        current_id = ctx.current_project.id if ctx.current_project else -1

        for p in projects:
            status = "Active" if p.id == current_id else ""
            table.add_row(str(p.id), p.name, str(p.created_at), status)
        
        console.print()
        console.print(table)
        console.print()

    else:
        print("Usage: show [options|module|sessions|projects]")

def cmd_list(ctx: Context, arg: str):
    """
    List command to show modules summary.
    """
    cmd_list_modules(ctx, 'all')

def cmd_import(ctx: Context, arg: str):
    """
    Import a module from a YAML file.
    Usage: import module <filepath>
    """
    args = arg.split(maxsplit=1)
    if len(args) != 2:
        print("Usage: import module <filepath>")
        return

    type_, source_path = args[0].lower(), args[1]
    
    if type_ != 'module':
        print("Invalid type. Use 'module'.")
        return
        
    if not os.path.exists(source_path):
        print(f"File not found: {source_path}")
        return

    # Validate YAML
    from core.schema import validate_yaml
    try:
        with open(source_path, 'r') as f:
            data = yaml.safe_load(f)
            validate_yaml(data)
    except Exception as e:
        print(f"Invalid YAML file: {e}")
        return

    # Determine destination
    root = get_project_root()
    dest_dir = root / "modules" / "custom"
        
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    filename = os.path.basename(source_path)
    dest_path = dest_dir / filename
    
    # Check if source is already in the destination
    source_abs = os.path.abspath(source_path)
    dest_abs = os.path.abspath(dest_path)
    
    if source_abs == dest_abs:
        console.print(f"[yellow]Module is already in the modules directory: {dest_path}[/yellow]")
        console.print("[yellow]Reloading modules...[/yellow]")
        
        # Just reload without copying
        ctx.tool_manager.load_yaml_modules(root_dirs=[str(root / "modules"), str(root / "workflows")])
        console.print("[green][+] Modules reloaded successfully.[/green]")
        return
    
    try:
        shutil.copy(source_path, dest_path)
        console.print(f"[green][+] Module imported to: {dest_path}[/green]")
        
        # Reload
        ctx.tool_manager.load_yaml_modules(root_dirs=[str(root / "modules"), str(root / "workflows")])
             
        console.print("[green][+] Modules reloaded successfully.[/green]")
        
    except Exception as e:
        console.print(f"[red]Error importing file: {e}[/red]")

    else:
        # print("Usage: show [options|modules|sessions|projects]")
        pass

def cmd_help(ctx: Context, arg: str):
    table = Table(
    title="[red]Core Commands[/red]",
    show_header=True,
    header_style="bold cyan",
    show_lines=True,
    box=box.ROUNDED,          # Makes corners round and smooth
    border_style="white" # Makes the lines yellow
)
    table.add_column("[red]Command[/red]", style="bold cyan", justify="center")
    table.add_column(
    Text("Description", justify="center"), # Centers the header text
    header_style="bold red",
    style="bold white",
    justify="left"                         # Aligns the column data left
)
    help_data = [
        ("use", "Select a module by name"),
        ("back", "Move back from the current context"),
        ("set", "Set a context-specific variable to a value"),
        ("run", "Execute the module (-j/-d for background)"),
        ("show", "Displays options, modules, projects, etc."),
        ("options", "Displays options for the active module"),
        ("search", "Search modules (regex)"),
        ("info", "Display YAML configuration for a module"),
        ("project", "Switch project(add -c for create and -d for delete )"),
        ("sessions", "Manage background sessions"),
        ("ls", "List files for current project"),
        ("cat","view file contents in current project "),
        ("bcat","view file as formatted table (JSON) or text"),
        ("import","Import a module from a YAML file"),
        ("help", "Help menu"),
        ("settings", "Open settings menu"),
        ("exit", "Exit the console"),
    ]

    for cmd, desc in help_data:
        table.add_row(cmd, desc)
    
    console.print()
    console.print(table)
    console.print()

from rich.syntax import Syntax
import os
import shutil

def cmd_create_project(ctx: Context, arg: str):
    """
    Refactored 'project' command.
    Usage:
      project           -> List projects
      project -c <name> -> Create project
      project <name|id> -> Select project
    """
    if not arg:
        cmd_show(ctx, 'projects')
        return

    args = arg.split()
    if args[0] == '-c':
        if len(args) < 2:
            print("Usage: project -c <name>")
            return
        name = args[1]
        proj = ctx.project_manager.create_project(name)
        if proj:
            ctx.current_project = proj
            print(f"✅ Project '{proj.name}' created and active.")
        return

    if args[0] == '-d':
        if len(args) < 2:
            print("Usage: project -d <name>")
            return
        
        target_name = args[1]
        p_repo = ctx.project_repo
        
        # Resolve project
        project_to_delete = p_repo.get_by_name(target_name)
        if not project_to_delete and target_name.isdigit():
             project_to_delete = p_repo.get(int(target_name))
             
        if not project_to_delete:
            print(f"[-] Project '{target_name}' not found.")
            return

        # Confirmation
        console.print(f"[bold red]WARNING:[/bold red] You are about to delete project '{project_to_delete.name}' and ALL its files.")
        console.print(f"Path: {project_to_delete.path}")
        confirm = input("Are you sure? [y/N] ").strip().lower()
        
        if confirm == 'y':
            # Delete files
            try:
                if os.path.exists(project_to_delete.path):
                    shutil.rmtree(project_to_delete.path)
                    console.print(f"[+] Files at {project_to_delete.path} deleted.")
                else:
                    console.print(f"[yellow][!] Path {project_to_delete.path} did not exist.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error deleting files: {e}[/red]")
                # We continue to delete DB record even if file deletion fails?
                # Probably best to continue or ask? 
                # Strict interpretation: "delete it". I'll proceed.

            # Delete DB
            if p_repo.delete(project_to_delete.id):
                console.print(f"✅ Project '{project_to_delete.name}' database record deleted.")
            else:
                 console.print(f"[red]Error deleting project from database.[/red]")

            # Reset active project if it was the one deleted
            if ctx.current_project and ctx.current_project.id == project_to_delete.id:
                ctx.current_project = None
                console.print("[yellow]Active project was deleted. Switched to None.[/yellow]")
        else:
            print("Deletion cancelled.")
        return

    # Select project by name or ID
    target = args[0]
    p_repo = ctx.project_repo
    selected = None
    
    # Try ID first
    if target.isdigit():
        pid = int(target)
        selected = p_repo.get(pid)
    
    # Try Name
    if not selected:
        selected = p_repo.get_by_name(target)
    
    if selected:
        ctx.current_project = selected
        print(f"[+] Switched to project '{selected.name}'")
    else:
        print(f"[-] Project '{target}' not found.")

def cmd_ls(ctx: Context, arg: str):
    """List files from current project organized by module"""
    if not ctx.current_project:
        console.print("[red][-] No active project. Use 'project <name>' first.[/red]")
        return
    
    project_path = ctx.current_project.path
    
    if not os.path.exists(project_path):
        console.print("[yellow]Project directory not found.[/yellow]")
        return
    
    # Scan filesystem for module directories
    files_data = []
    
    for item in os.listdir(project_path):
        item_path = os.path.join(project_path, item)
        
        # Skip hidden directories and non-directories
        if item.startswith('.') or not os.path.isdir(item_path):
            continue
        
        module_name = item
        
        # Scan for .txt files in module directory
        for file in os.listdir(item_path):
            if not file.endswith('.txt'):
                continue
            
            file_path = os.path.join(item_path, file)
            step_name = file.replace('.txt', '')
            
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            mtime = stat.st_mtime
            
            # Calculate line count
            try:
                with open(file_path, 'r') as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = 0
            
            # Format time (HH:MM)
            from datetime import datetime
            scan_time = datetime.fromtimestamp(mtime).strftime("%H:%M")
            
            # Format size (human readable)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size // 1024} KB"
            else:
                size_str = f"{file_size // (1024 * 1024)} MB"
            
            files_data.append({
                'module': module_name,
                'step': step_name,
                'size': size_str,
                'lines': line_count,
                'time': scan_time
            })
    
    if not files_data:
        console.print("[yellow]No output files found in this project.[/yellow]")
        return
    
    # Create table
    table = Table(
        title=f"Project: {ctx.current_project.name}",
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Module", style="green", justify="left")
    table.add_column("Step", style="cyan", justify="left")
    table.add_column("Size", style="yellow", justify="right")
    table.add_column("Lines", style="magenta", justify="right")
    table.add_column("Scan Time", style="blue", justify="center")
    
    # Add rows
    for file_info in files_data:
        table.add_row(
            file_info['module'],
            file_info['step'],
            file_info['size'],
            str(file_info['lines']),
            file_info['time']
        )
    
    console.print()
    console.print(table)
    console.print()

def cmd_cat(ctx: Context, arg: str):
    """Display raw file content (no formatting)"""
    if not ctx.current_project:
        console.print("[red]No active project. Use 'project <name>' first.[/red]")
        return
    
    if not arg:
        print("Usage: cat <module>/<file> or cat <file>")
        return

    project_path = ctx.current_project.path
    file_path = None
    
    # Parse argument: module/file or just file
    if '/' in arg:
        # Format: module/file
        parts = arg.split('/', 1)
        module_name = parts[0]
        filename = parts[1]
        
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        file_path = os.path.join(project_path, module_name, filename)
    else:
        # Search all modules for the file
        search_name = arg if arg.endswith('.txt') else f"{arg}.txt"
        
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                potential_path = os.path.join(item_path, search_name)
                if os.path.exists(potential_path):
                    file_path = potential_path
                    break
    
    if not file_path or not os.path.exists(file_path):
        console.print(f"[red]File not found: {arg}[/red]")
        console.print("[dim]Usage: cat <module>/<file> or cat <filename>[/dim]")
        return
    
    # Read and display raw content
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Print raw content without any formatting
        print(content)
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")


def cmd_bcat(ctx: Context, arg: str):
    """Display file as formatted table (if JSON) or text - Beautiful Cat"""
    if not ctx.current_project:
        console.print("[red]No active project. Use 'project <name>' first.[/red]")
        return
    
    if not arg:
        print("Usage: bcat <module>/<file> or bcat <file>")
        return

    project_path = ctx.current_project.path
    file_path = None
    
    # Parse argument: module/file or just file
    if '/' in arg:
        # Format: module/file
        parts = arg.split('/', 1)
        module_name = parts[0]
        filename = parts[1]
        
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        file_path = os.path.join(project_path, module_name, filename)
    else:
        # Search all modules for the file
        search_name = arg if arg.endswith('.txt') else f"{arg}.txt"
        
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                potential_path = os.path.join(item_path, search_name)
                if os.path.exists(potential_path):
                    file_path = potential_path
                    break
    
    if not file_path or not os.path.exists(file_path):
        console.print(f"[red]File not found: {arg}[/red]")
        console.print("[dim]Usage: bcat <module>/<file> or bcat <filename>[/dim]")
        return
    
    # Use server-side file reader
    data = file_reader.read_output_file(file_path)
    
    if not data['exists']:
        console.print(f"[red]File not found: {arg}[/red]")
        return
    
    # Display metadata header
    from rich.panel import Panel
    header_lines = []
    rel_path = os.path.relpath(file_path, project_path)
    header_lines.append(f"[bold cyan]File:[/bold cyan] {rel_path}")
    
    if data['metadata']:
        metadata = data['metadata']
        
        if 'timestamp' in metadata:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(metadata['timestamp'])
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                header_lines.append(f"[bold cyan]Executed:[/bold cyan] {time_str}")
            except:
                pass
        
        if 'duration_seconds' in metadata:
            header_lines.append(f"[bold cyan]Duration:[/bold cyan] {metadata['duration_seconds']}s")
        
        if 'tool' in metadata:
            header_lines.append(f"[bold cyan]Tool:[/bold cyan] {metadata['tool']}")
        
        if 'has_json' in metadata and metadata['has_json']:
            header_lines.append(f"[bold green]✓ JSON:[/bold green] {metadata.get('record_count', 0)} records")
        else:
            header_lines.append(f"[bold yellow]⚠ JSON:[/bold yellow] Not available (showing raw text)")
    
    if header_lines:
        header_text = "\n".join(header_lines)
        console.print(Panel(header_text, border_style="cyan", padding=(0, 1)))
        console.print()
    
    # Check if JSON available
    if data['has_json'] and data['json_data']:
        # Use server-side formatter
        table_data = formatter.format_as_table_data(data['json_data'])
        
        if table_data['total'] == 0:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        # Render table (CLI-specific rendering)
        result_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        
        # Add columns
        for col in table_data['columns']:
            result_table.add_column(col.title(), style="white")
        
        # Add rows (limit to 100 for display)
        display_limit = 100
        for i, row in enumerate(table_data['rows']):
            if i >= display_limit:
                break
            result_table.add_row(*row)
        
        console.print(result_table)
        
        # Show summary
        if table_data['total'] > display_limit:
            console.print(f"\n[dim]Showing {display_limit} of {table_data['total']} records[/dim]")
        else:
            console.print(f"\n[dim]Total: {table_data['total']} records[/dim]")
    else:
        # Fallback to raw text display
        console.print("[yellow]No JSON data available. Displaying raw text:[/yellow]\n")
        
        lines = data['raw_text'].strip().splitlines()
        result_table = Table(box=None, show_header=False, padding=(0, 1))
        result_table.add_column("Content", style="white")
        
        for line in lines[:100]:  # Limit to first 100 lines
            result_table.add_row(line)
        
        console.print(result_table)
        
        if len(lines) > 100:
            console.print(f"\n[dim]... {len(lines) - 100} more lines (showing first 100)[/dim]")


def cmd_list_modules(ctx: Context, mode: str):
    """
    mode: 'modules' | 'all'
    """
    if mode == 'all':
         # Just print summary, do NOT set context
         mods = ctx.tool_manager.list_modules()
         
         console.print(f"\n[bold cyan]Modules:[/bold cyan]")
         for i, m in enumerate(mods):
             console.print(f"{i+1}. {m}")
         console.print()
         return

    # Specific Mode -> Sets context
    items = ctx.tool_manager.list_modules()
    title = "Modules"
        
    if not items:
        print(f"No {title.lower()} found.")
        ctx.last_shown_map = []
        return

    # Set Context
    ctx.last_shown_map = items
    ctx.last_shown_type = 'module'

    table = Table(title="[red]"+title+"[/red]", show_header=True)
    table.add_column("[bold cyan]ID[/bold cyan]", style="bold cyan", justify="center")
    table.add_column("[bold green]Name[/bold green]", style="bold green", justify="left")
    table.add_column("[bold yellow]Tag[/bold yellow]", style="bold yellow", justify="left")
    table.add_column("[bold white]Description[/bold white]", style="bold white", justify="left")

    for i, path in enumerate(items):
        try:
            mod_cls = ctx.tool_manager.modules[path]
            meta = getattr(mod_cls, 'meta', {})
            
            module_id = meta.get('id', 'Unknown')
            tag = meta.get('tag', '')
            desc = meta.get('description', '')
            table.add_row(str(i+1), module_id, tag, desc)
        except Exception:
             table.add_row(str(i+1), "Error", "", "Error loading metadata")

    console.print()
    console.print(table)
    console.print()


def cmd_search(ctx: Context, arg: str):
    if not arg:
        print("Usage: search <regex>")
        return

    results = ctx.tool_manager.search_modules(arg)
    if not results:
        print("No matching modules found.")
        return
    
    table = Table(title=f"Search Results: {arg}", show_header=True, header_style="bold cyan")
    table.add_column("[red]ID[/red]", style="bold blue", justify="right")
    table.add_column("[red]Name[/red]", style="bold white")
    table.add_column("[red]Tag[/red]", style="bold yellow")
    table.add_column("[red]Description[/red]", style="dim white")
    
    for idx, path, meta in results:
        table.add_row(
            str(idx+1), 
            meta.get('id', 'Unknown'), 
            meta.get('tag', ''),
            meta.get('description', '')
        )
    
    console.print()
    console.print(table)
    console.print()


def cmd_options(ctx: Context, arg: str):
    """Alias for 'show options'"""
    cmd_show(ctx, 'options')

def cmd_info(ctx: Context, arg: str):
    """Display YAML configuration for a module to understand what happens behind the scenes
    Usage: info <module-name>
    """
    if not arg:
        console.print("\n[bold red]❌ Usage:[/bold red] [cyan]info <module-name>[/cyan]")
        console.print("[dim]💡 Example: info port-scan[/dim]\n")
        return
    
    # Resolve module
    target_path = arg
    
    # Check if arg is an ID
    if arg.isdigit():
        idx = int(arg) - 1
        
        if not ctx.last_shown_map:
            console.print("[yellow]⚠️  Please run 'show module' or 'search' first (IDs change depending on context).[/yellow]")
            return
            
        if 0 <= idx < len(ctx.last_shown_map):
            target_path = ctx.last_shown_map[idx]
        else:
            console.print(f"[red]❌ Invalid ID: {arg}. Range is 1-{len(ctx.last_shown_map)}[/red]")
            return
    
    # Get module
    module = ctx.tool_manager.get_module(target_path)
    if not module:
        console.print(f"\n[red]❌ Module '{arg}' not found.[/red]")
        console.print("[dim]💡 Use 'show module' or 'search <pattern>' to find modules.[/dim]\n")
        return
    
    # Check if module has yaml_path
    if not hasattr(module, 'yaml_path') or not module.yaml_path:
        console.print(f"[yellow]⚠️  Module '{arg}' does not have a YAML configuration file.[/yellow]")
        return
    
    yaml_path = module.yaml_path
    
    # Check if file exists
    if not os.path.exists(yaml_path):
        console.print(f"[red]❌ YAML file not found: {yaml_path}[/red]")
        return
    
    # Read and display YAML content
    try:
        with open(yaml_path, 'r') as f:
            yaml_content = f.read()
        
        # Get module metadata
        from rich.panel import Panel
        from rich.text import Text
        module_name = module.meta.get('name', 'Unknown')
        module_id = module.meta.get('id', 'Unknown')
        module_desc = module.meta.get('description', 'No description')
        module_author = module.meta.get('author', 'Unknown')
        module_tag = module.meta.get('tag', 'general')
        
       
        
        # Create info table
        info_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
        info_table.add_column("Key", style="bold yellow", width=15)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("📦 Module", f"[bold green]{module_name}[/bold green]")
        info_table.add_row("🆔 ID", f"[bold cyan]{module_id}[/bold cyan]")
        info_table.add_row("🏷️  Tag", f"[bold magenta]{module_tag}[/bold magenta]")
        info_table.add_row("👤 Author", f"[bold blue]{module_author}[/bold blue]")
        info_table.add_row("📝 Description", f"[dim white]{module_desc}[/dim white]")
        info_table.add_row("📂 Path", f"[dim cyan]{yaml_path}[/dim cyan]")
        
        # Center the table
        from rich.align import Align
        console.print(Align.center(info_table))
        console.print()

        
        # Create YAML content panel with custom styling
        console.print(Panel(
            "",
            title="[bold yellow]⚙️  YAML Configuration[/bold yellow]",
            border_style="yellow",
            padding=(0, 0)
        ))
        
        # Display YAML with enhanced syntax highlighting
        from rich.syntax import Syntax
        syntax = Syntax(
            yaml_content, 
            "yaml", 
            theme="dracula",  # Changed to dracula for better colors
            line_numbers=True,
            word_wrap=True,
            background_color="default"
        )
        console.print(syntax)
        
        # Footer with helpful tips
        console.print()
        console.print(Panel(
            "[dim]💡 Tip: Use [cyan]'use " + module_id + "'[/cyan] to load this module, then [cyan]'show options'[/cyan] to see available settings[/dim]",
            border_style="dim white",
            padding=(0, 1)
        ))
        console.print()
        
    except Exception as e:
        console.print(f"\n[red]❌ Error reading YAML file: {e}[/red]\n")

COMMANDS = {
    'use': cmd_use,
    'back': cmd_back,
    'set': cmd_set,
    'run': cmd_run,
    'exploit': cmd_run,
    'show': cmd_show,
    'project': cmd_create_project,
    'ls': cmd_ls,
    'cat': cmd_cat,
    'bcat': cmd_bcat,
    'help': cmd_help,
    'search': cmd_search,
    'options': cmd_options,
    'sessions': cmd_sessions,
    'settings': cmd_settings,
    'import': cmd_import,
    'list': cmd_list,
    'info': cmd_info,
}
