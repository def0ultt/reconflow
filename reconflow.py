from core.context import Context
from cli.shell import Shell

def main():
    # Initialize Core Context (Config, DB, Managers)
    context = Context()
    
    # Interactive Startup
    from cli.startup import run_startup_flow
    run_startup_flow(context)
    
    # Initialize and start CLI Shell
    shell = Shell(context)
    shell.start()

if __name__ == '__main__':
    main()