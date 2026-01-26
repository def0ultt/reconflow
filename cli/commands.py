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
        print(f"❌ Module '{arg}' not found.")

def cmd_back(ctx: Context, arg: str):
    ctx.active_module = None
    ctx.active_module_path = None

def cmd_set(ctx: Context, arg: str):
    if not ctx.active_module:
        print("❌ No active module. Use 'use <module>' first.")
        return

    parts = arg.split(maxsplit=1)
    if len(parts) != 2:
        print("Usage: set <option> <value>")
        return
    
    opt, val = parts[0].lower(), parts[1]
    if ctx.active_module.update_option(opt, val):
        print(f"{opt} => {val}")
    else:
        print(f"❌ Option '{opt}' not found.")

def cmd_run(ctx: Context, arg: str):
    if not ctx.active_module:
        print("❌ No active module.")
        return
    
    missing = ctx.active_module.validate_options()
    if missing:
        print(f"❌ Missing required options: {', '.join(missing)}")
        return
    
    try:
        ctx.active_module.run(ctx)
    except Exception as e:
        print(f"❌ Error running module: {e}")

def cmd_show(ctx: Context, arg: str):
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
    else:
        print("Usage: show [options|modules]")

def cmd_help(ctx: Context, arg: str):
    print("\nCore Commands\n=============\n")
    print("    Command       Description")
    print("    -------       -----------")
    print("    use           Select a module by name")
    print("    back          Move back from the current context")
    print("    set           Set a context-specific variable to a value")
    print("    run           Execute the module")
    print("    show          Displays options or modules")
    print("    options       Displays options for the active module")
    print("    list          List available modules")
    print("    search        Search modules (regex)")
    print("    project       Create/Switch project")
    print("    help          Help menu")
    print("    exit          Exit the console")
    print()

def cmd_create_project(ctx: Context, arg: str):
    if not arg:
        print("Usage: project <name>")
        return
    proj = ctx.project_manager.create_project(arg)
    if proj:
        ctx.current_project = proj
        print(f"✅ Project '{proj.name}' created and active.")

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
    'project': cmd_create_project,
    'help': cmd_help,
    'list': cmd_list,
    'search': cmd_search,
    'options': cmd_options,
}
