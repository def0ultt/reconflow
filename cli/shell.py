import cmd2
import argparse
import os
import sys
from typing import List, Optional
from rich.console import Console
from core.context import Context
from cli.commands import (
    cmd_use, cmd_back, cmd_set, cmd_run, cmd_show,
    cmd_import, cmd_search, cmd_cat, cmd_bcat, cmd_ls,
    cmd_settings, cmd_create_project, cmd_info, cmd_list_modules
)
from cli.session_cmd import cmd_sessions

console = Console()

class ReconFlowShell(cmd2.Cmd):
    """
    ReconFlow Command Line Interface based on cmd2.
    """
    def __init__(self, context: Context):
        # Initialize cmd2 with persistent history
        super().__init__(
            allow_cli_args=False,
            persistent_history_file=os.path.expanduser("~/.reconflow_history"),
        )
        self.context = context
        self.intro = "[bold cyan]Welcome to ReconFlow[/bold cyan]\nType 'help' or '?' for commands.\n"
        self.prompt = "reconflow> "
        
        # Remove built-in commands we don't need or want to override
        if 'edit' in self.get_visible_commands():
             del cmd2.Cmd.do_edit
        if 'py' in self.get_visible_commands():
             del cmd2.Cmd.do_py
        if 'ipy' in self.get_visible_commands():
             del cmd2.Cmd.do_ipy
        
        # Aliases
        self.aliases['ls'] = 'list_files'
        self.aliases['ll'] = 'list_files'
        self.aliases['exit'] = 'quit' 
        self.aliases['options'] = 'show options'
        
        self.hidden_commands.append('alias')
        self.hidden_commands.append('macro')
        self.hidden_commands.append('run_pyscript')
        self.hidden_commands.append('run_script')
        self.hidden_commands.append('shell')
        self.hidden_commands.append('shortcuts')

    def _update_prompt(self):
        """Dynamic prompt generation based on context."""
        style_list = []
        if self.context.current_project:
            # Mint green / Cyan for project
            proj_str = f"[bold #00fab4]➜ {self.context.current_project.name}[/bold #00fab4]"
            style_list.append(proj_str)
        
        prompt_str = "reconflow"
        
        mod_part = ""
        if hasattr(self.context, 'active_module_path') and self.context.active_module_path:
             # Light purple for module
             mod_part = f" [italic #afafff]({self.context.active_module_path})[/italic #afafff]"
             
        proj_part = f"{' '.join(style_list)} " if style_list else ""
        
        # Structure: [Project] reconflow (Module) >
        # We use rich to render the prompt string with ANSI codes
        
        from rich.console import Console
        with open(os.devnull, 'w') as devnull:
            c = Console(force_terminal=True, color_system="truecolor", file=devnull)
            
            # Capture the styled prompt
            with c.capture() as capture:
                 c.print(f'{proj_part}[bold #5fafff]{prompt_str}[/bold #5fafff]{mod_part} [bold #5fafff]❯[/bold #5fafff] ', end='')
        
        self.prompt = capture.get()

    def postcmd(self, stop: bool, line: str) -> bool:
        """Hook that runs after every command."""
        self._update_prompt()
        return stop

    def preloop(self):
        """Hook that runs before the command loop starts."""
        self._update_prompt()

    # --- Core Commands ---

    def do_use(self, arg):
        """Select a module by name or ID (from 'show modules')."""
        cmd_use(self.context, arg)

    def complete_use(self, text, line, begidx, endidx):
        """Autocomplete for 'use' command."""
        modules = self.context.tool_manager.list_modules()
        if not text:
            return modules
        return [m for m in modules if m.startswith(text)]

    def do_back(self, arg):
        """Move back from the current context."""
        cmd_back(self.context, arg)

    def do_set(self, arg):
        """Set a context-specific variable to a value."""
        cmd_set(self.context, arg)

    def complete_set(self, text, line, begidx, endidx):
        """Autocomplete for 'set' command."""
        if not self.context.active_module:
            return []
        options = list(self.context.active_module.options.keys())
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    def do_run(self, arg):
        """
        Execute the module.
        Usage: run [-j] [-d]
        -j, -d: Run in background (detached)
        """
        cmd_run(self.context, arg)

    def do_exploit(self, arg):
        """Alias for run."""
        cmd_run(self.context, arg)

    # Dictionary for 'show' subcommands completion
    show_subcommands = ['options', 'modules', 'sessions', 'projects']

    def do_show(self, arg):
        """
        Displays options, modules, projects, etc.
        Usage: show [options|modules|sessions|projects]
        """
        cmd_show(self.context, arg)

    def complete_show(self, text, line, begidx, endidx):
        """Autocomplete for 'show' command."""
        if not text:
            return self.show_subcommands
        return [s for s in self.show_subcommands if s.startswith(text)]

    def do_search(self, arg):
        """Search modules (regex)."""
        cmd_search(self.context, arg)

    def do_info(self, arg):
        """Display YAML configuration and details for a module."""
        cmd_info(self.context, arg)

    def do_list(self, arg):
        """List modules."""
        cmd_list_modules(self.context, 'all')

    def do_project(self, arg):
        """
        Switch project or create/delete.
        Usage: 
            project <name|id>
            project -c <name>
            project -d <name>
        """
        cmd_create_project(self.context, arg)

    def complete_project(self, text, line, begidx, endidx):
        """Autocomplete for 'project' command."""
        flags = ['-c', '-d']
        try:
            projects = [p.name for p in self.context.project_repo.get_all()]
        except:
            projects = []
        
        options = flags + projects
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    def do_sessions(self, arg):
        """Manage background sessions."""
        cmd_sessions(self.context, arg)

    def do_list_files(self, arg):
        """List files for current project. Alias: ls, ll"""
        cmd_ls(self.context, arg)

    def do_cat(self, arg):
        """View file contents in current project."""
        cmd_cat(self.context, arg)

    def complete_cat(self, text, line, begidx, endidx):
        """Autocomplete for 'cat' command (files)."""
        return self._complete_project_files(text)

    def _complete_project_files(self, text):
        """Helper to find files in project."""
        matches = []
        if not self.context.current_project:
            return []
            
        root = self.context.current_project.path
        if not os.path.exists(root):
            return []
            
        for root_dir, dirs, files in os.walk(root):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root_dir, f), root)
                if rel_path.startswith(text):
                    matches.append(rel_path)
        return matches

    def do_bcat(self, arg):
        """View file as formatted table (JSON) or text."""
        cmd_bcat(self.context, arg)
    
    def complete_bcat(self, text, line, begidx, endidx):
        return self._complete_project_files(text)

    def do_import(self, arg):
        """Import a module from a YAML file."""
        cmd_import(self.context, arg)

    def do_settings(self, arg):
        """Open settings menu."""
        cmd_settings(self.context, arg)
        self._update_prompt()

    # --- Overrides ---

    def sigint_handler(self, signum, frame):
        """
        Handle Ctrl+C (SIGINT). 
        Prompt user to exit explicitly.
        """
        console.print("\n[bold red][!] To exit, please type 'exit'[/bold red]")
        self._update_prompt()
        print(self.prompt, end='', flush=True)

    def default(self, statement):
        """
        Called when parsing fails.
        """
        console.print(f"[red]Unknown command: {statement.command}[/red]")
        console.print("[dim]Type 'help' for a list of commands.[/dim]")

    def do_help(self, arg):
        """
        List available commands or provide detailed help for a specific command.
        Usage: help [command]
        """
        if arg:
            super().do_help(arg)
            return

        # Custom Help Dashboard - Sectional Layout
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        from rich.align import Align
        from rich.console import Group

        # Define Sections
        # Format: (title, [(cmd, desc), ...])
        
        sections = [
            ("Core Commands", [
                ("list", "List available modules"),
                ("search", "Search modules by keyword/regex"),
                ("use", "Select a module to work with"),
                ("back", "Unselect module / Go back"),
                ("history", "View command history"),
                ("clear", "Clear the screen"),
                ("help", "Show this help message"),
                ("exit", "Exit ReconFlow"),
            ]),
            ("Module Commands", [
                ("run", "Execute the active module (alias: exploit)"),
                ("set", "Set module options/variables"),
                ("show", "Show options, modules, projects"),
                ("info", "View module details and YAML"),
                ("import", "Import custom YAML modules"),
                ("ls", "List files in current project (alias for list_files)"),
                ("cat", "View file content in project"),
                ("bcat", "View JSON/Text files with filtering"),
            ]),
             ("Job Commands", [
                ("sessions", "Manage background sessions"),
                # run -d is a flag, not a separate command, but listed here as context
            ]),
            ("Project Commands", [
                ("project", "Manage projects (create, switch, delete)"),
                # User mentioned 'project -d' example in comments
            ]),
            ("Configuration", [
                ("settings", "Configure global settings/API keys"),
            ]),
        ]

        console.print()
        
        for title, cmds in sections:
            # Print Header
            console.print(f"[bold magenta]{title}[/bold magenta]")
            console.print(f"[magenta]{'=' * len(title)}[/magenta]")
            console.print()
            
            # Create Section Table
            # Borderless, clean, but with header underline
            table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan", padding=(0, 2), collapse_padding=True)
            table.add_column("Command", style="bold yellow", justify="left", width=20)
            table.add_column("Description", style="bold white", justify="left")
            
            for c, desc in cmds:
                table.add_row(c, desc)
                
            console.print(table)
            console.print() # Spacer after section

        console.print("   [dim]Tip: use 'help <command>' for detailed docs.[/dim]")
        console.print()
