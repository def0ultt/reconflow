from core.context import Context
from rich.console import Console
from rich.table import Table

console = Console()

def cmd_use(ctx: Context, arg: str):
    if not arg:
        print("Usage: use <module_path>")
        return
    
    target_path = arg
    # Check if arg is an ID
    if arg.isdigit():
        idx = int(arg) - 1 # 1-based to 0-based
        path = ctx.tool_manager.get_module_by_id(idx)
        if path:
            target_path = path

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
    if ctx.active_module.update_option(opt, val):
        print(f"{opt} => {val}")
    else:
        print(f" Option '{opt}' not found.")


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
        table.add_column("Description", style="white")

        for name, opt in ctx.active_module.options.items():
            table.add_row(name, str(opt.value), str(opt.required), opt.description)
        
        console.print(table)
    
    elif arg == 'modules':
        cmd_list_modules(ctx, "")

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

    elif arg == 'workflows':
        workflows = ctx.workflow_manager.list_workflows()
        if not workflows:
            print("No workflows found.")
            return
        
        table = Table(title="Workflows", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green", justify="center")
        table.add_column("Steps", style="magenta", justify="center")
        
        for name, steps in workflows.items():
            table.add_row(name, str(len(steps)))
        
        console.print()
        console.print(table)
        console.print()

    else:
        print("Usage: show [options|modules|sessions|projects|workflows]")

def cmd_help(ctx: Context, arg: str):
    table = Table(title="Core Commands", show_header=True, header_style="bold cyan",show_lines=True)
    table.add_column("Command", style="bold cyan", justify="left")
    table.add_column("Description", style="bold white", justify="left" )

    help_data = [
        ("use", "Select a module by name"),
        ("back", "Move back from the current context"),
        ("set", "Set a context-specific variable to a value"),
        ("run", "Execute the module (-j/-d for background)"),
        ("show", "Displays options, modules, projects, etc."),
        ("options", "Displays options for the active module"),
        ("search", "Search modules (regex)"),
        ("project", "Create/Switch project"),
        ("sessions", "Manage background sessions"),
        ("ls", "List files for current project"),
        ("cat","view file contents in  current project "),
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

def cmd_list_modules(ctx: Context, arg: str):
    modules = ctx.tool_manager.list_modules()
    if not modules:
        print("No modules found.")
        return

    table = Table(title="Available Modules", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Path", style="magenta", justify="center")
    table.add_column("Name", style="green", justify="center")
    table.add_column("Description", style="white", justify="center")

    for i, path in enumerate(modules):
        try:
            mod_cls = ctx.tool_manager.modules[path]
            meta = getattr(mod_cls, 'meta', {})
            name = meta.get('name', 'Unknown')
            desc = meta.get('description', '')
            table.add_row(str(i+1), path, name, desc)
        except Exception:
             table.add_row(str(i+1), path, "Error", "Could not load metadata")

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
    table.add_column("[red]Description[/red]", style=" white")
    
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
}
