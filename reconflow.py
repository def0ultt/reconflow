from core.context import Context
from cli.shell import ReconFlowShell

def main():
    # Initialize Core Context (Config, DB, Managers)
    context = Context()
    
    # Interactive Startup
    from cli.startup import run_startup_flow
    run_startup_flow(context)
    
    # Initialize and start CLI Shell
    shell = ReconFlowShell(context)
    shell.cmdloop()

if __name__ == '__main__':
    main()