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
        self.completer = Completer().get_completer()
        self.style = Style.from_dict({
            'prompt': '#00ff00 bold',
            'project': '#00aaff',
        })
        self.session = PromptSession(
            completer=self.completer,
            style=self.style
        )
    
    def get_prompt(self):
        style_list = []
        if self.context.current_project:
            style_list.append(f"[{self.context.current_project.name}]")
        
        prompt_str = "reconflow"
        if hasattr(self.context, 'active_module_path') and self.context.active_module_path:
             prompt_str += f" ({self.context.active_module_path})"
             
        padding = " " if not style_list else " " # fix padding logic simplified
        
        # simplified HTML construction
        proj_part = f'<project>{" ".join(style_list)}</project> ' if style_list else ""
        return HTML(f'{proj_part}<prompt>{prompt_str}></prompt> ')

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
                    print(f"❌ Unknown command: {cmd}")

            except (KeyboardInterrupt, EOFError):
                break
