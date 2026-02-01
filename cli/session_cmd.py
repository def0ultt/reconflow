import argparse
from rich.console import Console
from rich.table import Table
from core.context import Context

console = Console()

def cmd_sessions(ctx: Context, arg: str):
    parser = argparse.ArgumentParser(prog="sessions", description="Manage background sessions")
    parser.add_argument("-a", "--all", action="store_true", help="Show all sessions (active and historic)")
    parser.add_argument("-s", "--stop", metavar="ID", type=int, help="Stop a session")
    parser.add_argument("-k", "--kill", metavar="ID", type=int, help="Kill a session (alias for stop)")
    parser.add_argument("-i", "--interact", metavar="ID", type=int, help="Interact with a session (not implemented)")
    
    # Parse args manually because argparse expects sys.argv
    try:
        args = parser.parse_args(arg.split() if arg else [])
    except SystemExit:
        return

    if args.stop or args.kill:
        sid = args.stop or args.kill
        if ctx.session_manager.stop_session(sid):
            print(f"[*] Stopping session {sid}...")
        else:
            print(f"[-] Session {sid} not found or not active.")
        return

    # Default action: List sessions
    # Filter by project unless -a is passed? 
    # For now, list all for current project if active, or all if -a
    
    if not ctx.current_project:
        print("[-] No active project. Sessions are tied to projects.")
        return

    sessions = ctx.session_manager.list_sessions(project_id=ctx.current_project.id)
    
    # Filter for active only if -a is NOT present? 
    # User request: "sessions -a : two show all session"
    # So default (no args) should probably show active only?
    # Logic:
    # -a : Show ALL (running, completed, stopped, failed)
    # Default: Show RUNNING only
    
    if not args.all:
        sessions = [s for s in sessions if s.status == "running"]

    if not sessions:
        print("No active sessions.")
        return

    table = Table(title=f"Active Sessions" if not args.all else "All Sessions", box=None, show_header=True, header_style="bold cyan")
    table.add_column("Id", style="blue", justify="right")
    table.add_column("Name", style="magenta")
    table.add_column("Target", style="bold blue") # Replaced 'Type' and 'Connection'
    table.add_column("Status", style="yellow")
    # Removed 'Information' column
    
    for s in sessions:
        table.add_row(
            str(s.id), 
            s.module,  # Module Name
            s.target or "", # User option set
            s.status
        )
    
    console.print()
    console.print(table)
    console.print()
