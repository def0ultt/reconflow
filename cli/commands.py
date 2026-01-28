from core.context import Context
from rich.console import Console
from rich.table import Table
import os
import shutil
import yaml
from utils.paths import get_project_root

console = Console()

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

def cmd_set(ctx: Context, arg: str):
    if not ctx.active_module:
        print(" No active module. Use 'use <module>' first.")
        return

    parts = arg.split(maxsplit=1)
    if len(parts) != 2:
        print("Usage: set <option> <value>")
        return
    
    opt, val = parts[0].lower(), parts[1]
    
    # Variable Substitution
    if val.startswith('$'):
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
        print(f"{opt} => {val}")
    else:
        print(f" Option '{opt}' not found.")
from workflow.engine import WorkflowRunner

def cmd_workflow(ctx: Context, arg: str):
    """
    Manage and run workflows.
    Usage:
      workflow list
      workflow run <name> [var=value ...]
    """
    if not arg:
        cmd_show(ctx, 'workflows')
        return

    args = arg.split()
    subcmd = args[0]
    
    if subcmd == 'list':
        cmd_show(ctx, 'workflows')
    
    elif subcmd == 'run':
        if len(args) < 2:
            print("Usage: workflow run <name> [key=value ...]")
            return
        
        wf_name = args[1]
        
        # Parse inputs
        inputs = {}
        for pair in args[2:]:
            if '=' in pair:
                k, v = pair.split('=', 1)
                inputs[k] = v
        
        runner = WorkflowRunner(ctx)
        try:
            runner.run_workflow(wf_name, inputs)
        except Exception as e:
            print(f"Error executing workflow: {e}")
            
    else:
        print("Unknown workflow command. Try 'list' or 'run'.")

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
            print(f"[*] Module running in background as session {session.id}")
    else:
        try:
            ctx.active_module.run(ctx)
        except Exception as e:
            print(f" Error running module: {e}")

def cmd_show(ctx: Context, arg: str):
    if not arg:
        print("Usage: show [options|modules|sessions|projects|workflows]")
        return
        
    if arg == 'options':
        if not ctx.active_module:
            print("No active module.")
            return
        
        table = Table(title=f"Module Options ({ctx.active_module.meta['name']})")
        table.add_column("Name", style="cyan")
        table.add_column("Current Setting", style="magenta")
        table.add_column("Required", style="green")
        table.add_column("Description", style="dim white")

        for name, opt in ctx.active_module.options.items():
            table.add_row(name, str(opt.value), str(opt.required), opt.description)
        
        console.print(table)
    
    elif arg in ('modules', 'module'):
        cmd_list_modules(ctx, 'modules')

    elif arg in ('workflows', 'workflow'):
        cmd_list_modules(ctx, 'workflows')

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
        print("Usage: show [options|module|workflow|sessions|projects]")

def cmd_list(ctx: Context, arg: str):
    """
    List command to show both workflows and modules summary.
    """
    cmd_list_modules(ctx, 'all')

def cmd_import(ctx: Context, arg: str):
    """
    Import a module or workflow from a YAML file.
    Usage: import <workflow|module> <filepath>
    """
    args = arg.split(maxsplit=1)
    if len(args) != 2:
        print("Usage: import <workflow|module> <filepath>")
        return

    type_, source_path = args[0].lower(), args[1]
    
    if type_ not in ['workflow', 'module']:
        print("Invalid type. Use 'workflow' or 'module'.")
        return
        
    if not os.path.exists(source_path):
        print(f"File not found: {source_path}")
        return

    # Validate YAML
    try:
        with open(source_path, 'r') as f:
            data = yaml.safe_load(f)
            if not data or 'metadata' not in data:
                 print("Invalid format: Missing 'metadata' block.")
                 return
    except Exception as e:
        print(f"Invalid YAML file: {e}")
        return

    # Determine destination
    root = get_project_root()
    if type_ == 'workflow':
        dest_dir = root / "workflows" / "custom"
    else:
        dest_dir = root / "modules" / "custom"
        
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    filename = os.path.basename(source_path)
    dest_path = dest_dir / filename
    
    try:
        shutil.copy(source_path, dest_path)
        print(f"✅ Imported to {dest_path}")
        
        # Reload
        if type_ == 'workflow':
             # Reload workflow manager and tool manager?
             ctx.workflow_manager.load_yaml_workflows()
             ctx.tool_manager.load_workflow_modules(root_dir=str(root / "workflows"))
        else:
             ctx.tool_manager.load_yaml_modules(root_dir=str(root / "modules"))
             
        print("[+] Reloaded system configs.")
        
    except Exception as e:
        print(f"Error importing file: {e}")

    else:
        print("Usage: show [options|modules|sessions|projects|workflows]")
from rich import box
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
    table.add_column("[red]Description[/red]", style="bold white", justify="left" )

    help_data = [
        ("use", "Select a module by name"),
        ("back", "Move back from the current context"),
        ("set", "Set a context-specific variable to a value"),
        ("run", "Execute the module (-j/-d for background)"),
        ("show", "Displays options, modules, projects, etc."),
        ("options", "Displays options for the active module"),
        ("search", "Search modules (regex)"),
        ("project", "Switch project(add -c for create and -d for delete )"),
        ("sessions", "Manage background sessions"),
        ("ls", "List files for current project"),
        ("cat","view file contents in  current project "),
        ("import","Import a module or workflow from a YAML file"),
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
    if not ctx.current_project:
        console.print("[red][-] No active project. Use 'project <name>' first.[/red]")
        return
    
    files = ctx.project_repo.get_files(ctx.current_project.id)
    if not files:
        console.print("[yellow]No files in this project.[/yellow]")
        return

    table = Table(title=f"Files in {ctx.current_project.name}",box=None,show_header=True, header_style="bold cyan")
    table.add_column("[red]Path[/red]", style="bold blue", justify="center")
    table.add_column("[red]Size (B)[/red]", style="bold white", justify="center")
    table.add_column("[red]Date[/red]", style="bold white", justify="center")

    project_root = ctx.current_project.path
    for f in files:
        # Calculate relative path
        try:
           rel_path = os.path.relpath(f.file_path, project_root)
        except ValueError:
           rel_path = f.file_path
        
        table.add_row(rel_path, str(f.file_size_bytes), str(f.created_at))
    
    console.print()
    console.print(table)
    console.print()

def cmd_cat(ctx: Context, arg: str):
    if not ctx.current_project:
        console.print("[red]No active project. Use 'project <name>' first.[/red]")
        return
    
    if not arg:
        print("Usage: cat <filename>")
        return

    filename = arg
    content = ctx.file_manager.get_file_content(ctx.current_project.id, filename)
    
    if content:
        console.print(f"[bold cyan][*] SQLite read file: {filename}[/bold cyan]")
        
        # Display as Table as requested
        # We try to detect structure. 
        # If simple lines, single column. 
        # If CSV-like (comma/tab), split it? 
        # For complexity, let's treat it as single column lines for now, or raw if JSON.
        
        lines = content.strip().splitlines()
        
        # JSON detection for pretty printing
        if filename.endswith('.json') or (content.strip().startswith('{') and content.strip().endswith('}')):
             syntax = Syntax(content, "json", theme="monokai", line_numbers=True)
             console.print(syntax)
             return

        # Table display for text files
        result_table = Table(box=None, show_header=False)
        result_table.add_column("Content", style="white")
        
        for line in lines:
            result_table.add_row(line)
        
        console.print(result_table)
    else:
        console.print(f"[red]File '{filename}' not found in project.[/red]")

def cmd_list_modules(ctx: Context, mode: str):
    """
    mode: 'modules' | 'workflows' | 'all'
    """
    if mode == 'all':
         # Just print summary, do NOT set context
         mods = ctx.tool_manager.list_pure_modules()
         wfs = ctx.tool_manager.list_workflow_modules()
         
         console.print(f"\n[bold cyan]Workflows ({len(wfs)}):[/bold cyan]")
         for i, m in enumerate(wfs):
             # We assume name-based display is allowed, but ID for referencing?
             # User said: "List ... Output example: 1. workflow/live_subdomain"
             console.print(f"{i+1}. {m}")
             
         console.print(f"\n[bold cyan]Modules ({len(mods)}):[/bold cyan]")
         for i, m in enumerate(mods):
             console.print(f"{i+1}. {m}")
         console.print()
         return

    # Specific Mode -> Sets context
    if mode == 'workflows':
        items = ctx.tool_manager.list_workflow_modules()
        title = "Workflows"
    else:
        items = ctx.tool_manager.list_pure_modules()
        title = "Modules"
        
    if not items:
        print(f"No {title.lower()} found.")
        ctx.last_shown_map = []
        return

    # Set Context
    ctx.last_shown_map = items
    ctx.last_shown_type = 'workflow' if mode == 'workflows' else 'module'

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Path/Name", style="green", justify="left")
    table.add_column("Description", style="white", justify="left")

    for i, path in enumerate(items):
        try:
            # We need to instantiate or peek class to get meta
            # For performance, maybe Manager should cache meta separate from instance?
            # Creating instance is okay for now.
            mod_cls = ctx.tool_manager.modules[path]
            # If it's a class, check meta attr
            meta = getattr(mod_cls, 'meta', {})
            # If it's generic yaml, meta might be on instance or class if we hacked it.
            # In my previous implementation I set DynamicYamlModule.meta = temp.meta
            
            desc = meta.get('description', '')
            table.add_row(str(i+1), path, desc)
        except Exception:
             table.add_row(str(i+1), path, "Error loading metadata")

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
    table.add_column("[red]Path[/red]", style="bold blue")
    table.add_column("[red]Name[/red]", style="bold white")
    table.add_column("[red]Description[/red]", style="dim white")
    
    for idx, path, meta in results:
        table.add_row(str(idx+1), path, meta.get('name', 'Unknown'), meta.get('description', ''))
    
    console.print()
    console.print(table)
    console.print()

def cmd_options(ctx: Context, arg: str):
    """Alias for 'show options'"""
    cmd_show(ctx, 'options')

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
    'help': cmd_help,
    'search': cmd_search,
    'options': cmd_options,
    'sessions': cmd_sessions,
    'settings': cmd_settings,
    'workflow': cmd_workflow,
    'import': cmd_import,
    'list': cmd_list,
}
