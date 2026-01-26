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
    # Filter by workspace unless -a is passed? 
    # For now, list all for current workspace if active, or all if -a
    
    if not ctx.current_workspace:
        print("[-] No active workspace. Sessions are tied to workspaces.")
        return

    sessions = ctx.session_manager.list_sessions(workspace_id=ctx.current_workspace.id)
    
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

    table = Table(title=f"Active Sessions" if not args.all else "All Sessions")
    table.add_column("Id", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Type", style="green") # Module name?
    table.add_column("Status", style="yellow")
    table.add_column("Information", style="white")
    table.add_column("Connection", style="blue") # Target

    for s in sessions:
        info = s.info if s.info else ""
        table.add_row(
            str(s.id), 
            "", # Name (placeholder)
            s.module, 
            s.status, 
            info,
            s.target or ""
        )
    
    console.print(table)
