from core.context import Context
from rich.console import Console
from rich.table import Table

console = Console()

def cmd_use(ctx: Context, arg: str):
    if not arg:
        print("Usage: use <module_path>")
        return
    
    module = ctx.tool_manager.get_module(arg)
    if module:
        ctx.active_module = module
        ctx.active_module_path = arg
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
        table = Table(title="Available Modules")
        table.add_column("Path", style="cyan")
        for m in ctx.tool_manager.list_modules():
            table.add_row(m)
        console.print(table)

    elif arg == 'sessions':
        cmd_sessions(ctx, "-a")

    elif arg == 'workspaces':
        workspaces = ctx.workspace_manager.list_workspaces()
        if not workspaces:
            print("No workspaces found.")
            return

        table = Table(title="Workspaces")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Created At", style="green")
        table.add_column("Status", style="white")

        current_id = ctx.current_workspace.id if ctx.current_workspace else -1

        for w in workspaces:
            status = "Active" if w.id == current_id else ""
            table.add_row(str(w.id), w.name, str(w.created_at), status)
        console.print(table)

    elif arg == 'workflows':
        workflows = ctx.workflow_manager.list_workflows()
        if not workflows:
            print("No workflows found.")
            return
        
        table = Table(title="Workflows")
        table.add_column("Name", style="cyan")
        table.add_column("Steps", style="magenta")
        
        for name, steps in workflows.items():
            table.add_row(name, str(len(steps)))
        console.print(table)

    else:
        print("Usage: show [options|modules|sessions|workspaces|workflows]")

def cmd_help(ctx: Context, arg: str):
    table = Table(title="Core Commands", box=None, show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bold blue")
    table.add_column("Description", style="white")

    help_data = [
        ("use", "Select a module by name"),
        ("back", "Move back from the current context"),
        ("set", "Set a context-specific variable to a value"),
        ("run", "Execute the module (-j/-d for background)"),
        ("show", "Displays options, modules, workspaces, etc."),
        ("options", "Displays options for the active module"),
        ("list", "List available modules"),
        ("search", "Search modules (regex)"),
        ("workspace", "Create/Switch workspace"),
        ("sessions", "Manage background sessions"),
        ("help", "Help menu"),
        ("exit", "Exit the console"),
    ]

    for cmd, desc in help_data:
        table.add_row(cmd, desc)
    
    console.print()
    console.print(table)
    console.print()

def cmd_create_workspace(ctx: Context, arg: str):
    if not arg:
        print("Usage: workspace <name>")
        return
    ws = ctx.workspace_manager.create_workspace(arg)
    if ws:
        ctx.current_workspace = ws
        print(f"✅ Workspace '{ws.name}' created and active.")

def cmd_list(ctx: Context, arg: str):
    modules = ctx.tool_manager.list_modules()
    if not modules:
        print("No modules found.")
        return

    table = Table(title="Available Modules")
    table.add_column("Path", style="cyan")
    for m in modules:
        table.add_row(m)
    console.print(table)

def cmd_search(ctx: Context, arg: str):
    if not arg:
        print("Usage: search <regex>")
        return

    results = ctx.tool_manager.search_modules(arg)
    if not results:
        print("No matching modules found.")
        return
    
    table = Table(title=f"Search Results: {arg}")
    table.add_column("Path", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="white")
    
    for path, meta in results:
        table.add_row(path, meta.get('name', 'Unknown'), meta.get('description', ''))
    
    console.print(table)

def cmd_options(ctx: Context, arg: str):
    """Alias for 'show options'"""
    cmd_show(ctx, 'options')

COMMANDS = {
    'use': cmd_use,
    'back': cmd_back,
    'set': cmd_set,
    'run': cmd_run,
    'exploit': cmd_run, # Alias
    'show': cmd_show,
    'workspace': cmd_create_workspace,
    'help': cmd_help,
    'list': cmd_list,
    'search': cmd_search,
    'options': cmd_options,
    'sessions': cmd_sessions,
}
