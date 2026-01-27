from prompt_toolkit.completion import Completer as PTCompleter, Completion
from .commands import COMMANDS

class Completer:
    """
    Autocomplete logic for the CLI.
    Wraps a custom PromptToolkit Completer.
    """
    def __init__(self, context):
        self.context = context
        self.pt_completer = ReconCompleter(context)
    
    def get_completer(self):
        return self.pt_completer

class ReconCompleter(PTCompleter):
    def __init__(self, context):
        self.context = context
        self.commands = list(COMMANDS.keys()) + ['exit']

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()
        
        # If empty or just spaces, show all commands? Or nothing?
        if not text.strip():
            return 

        # 1. Top-level commands
        # If we are typing the first word (and haven't finished it or just finished it but no space)
        if len(words) == 1 and not text.endswith(' '):
            for cmd in self.commands:
                if cmd.startswith(words[0]):
                    yield Completion(cmd, start_position=-len(words[0]))
        
        elif len(words) == 0:
             # Just started
             for cmd in self.commands:
                yield Completion(cmd, start_position=0)

        # 2. Arguments
        else:
            cmd = words[0]
            
            # Determine effective current word being typed
            if text.endswith(' '):
                current_word = ""
            else:
                current_word = words[-1]

            # Logic per command
            if cmd == 'project':
                # Suggest project names
                # We use project_repo here if possible or project_manager
                # context has project_repo
                # But project_manager.list_projects() returns objects
                
                # Fetch dynamically
                try:
                    projects = self.context.project_repo.get_all()
                    for p in projects:
                        if p.name.startswith(current_word):
                            yield Completion(p.name, start_position=-len(current_word))
                except Exception:
                    pass

            elif cmd == 'show':
                subcmds = ['options', 'modules', 'sessions', 'projects', 'workflows']
                for s in subcmds:
                    if s.startswith(current_word):
                        yield Completion(s, start_position=-len(current_word))
            
            elif cmd == 'cat':
                # Autocomplete files in current project
                if self.context.current_project:
                    try:
                        files = self.context.project_repo.get_files(self.context.current_project.id)
                        import os
                        for f in files:
                            fname = os.path.basename(f.file_path)
                            if fname.startswith(current_word):
                                yield Completion(fname, start_position=-len(current_word))
                    except Exception:
                         pass

            elif cmd == 'use':
                # Autocomplete modules
                # This could be heavy if many modules, but okay for now
                try:
                    modules = self.context.tool_manager.list_modules()
                    for m in modules:
                        if m.startswith(current_word):
                            yield Completion(m, start_position=-len(current_word))
                except Exception:
                    pass
