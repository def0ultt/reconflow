from core.context import Context
from cli.shell import Shell

def main():
    # Initialize Core Context (Config, DB, Managers)
    context = Context()
    
    # Initialize and start CLI Shell
    shell = Shell(context)
    shell.start()

if __name__ == '__main__':
    main()