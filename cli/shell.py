from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from core.context import Context
from .completer import Completer
from .commands import COMMANDS

class Shell:
    """
    Encapsulates the prompt_toolkit session and main loop.
    """
    def __init__(self, context: Context):
        self.context = context
        self.completer = Completer(context).get_completer()
        self.style = Style.from_dict({
            'prompt': '#5fafff bold',  # Lighter, more premium blue
            'project': 'bold #00fab4', # Mint green / Cyan for project
            'module': '#afafff italic', # Light purple for module
        })
        self.session = PromptSession(
            completer=self.completer,
            style=self.style
        )
    
    def get_prompt(self):
        style_list = []
        if self.context.current_project:
            style_list.append(f"➜ {self.context.current_project.name}")
        
        prompt_str = "reconflow"
        
        mod_part = ""
        if hasattr(self.context, 'active_module_path') and self.context.active_module_path:
             mod_part = f" <module>({self.context.active_module_path})</module>"
             
        proj_part = f'<project>{" ".join(style_list)}</project> ' if style_list else ""
        
        # Structure: [Project] reconflow (Module) >
        return HTML(f'{proj_part}<prompt>{prompt_str}</prompt>{mod_part} <prompt>❯</prompt> ')

    def start(self):
        print("Welcome to ReconFlow. Type 'help' for commands.")
        
        while True:
            try:
                user_input = self.session.prompt(self.get_prompt())
                if not user_input.strip():
                    continue

                parts = user_input.strip().split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == 'exit':
                    print("Goodbye!")
                    break
                
                if cmd in COMMANDS:
                    COMMANDS[cmd](self.context, arg)
                else:
                    print(f" Unknown command: {cmd}")

            except (KeyboardInterrupt, EOFError):
                break
